# coding=utf-8

import logging
import socket
import struct

import cryptor
from base import TcpProtocol, UdpProtocol


class ClientProtocol(TcpProtocol):
    def __init__(self, *args):
        super().__init__(*args)
        self.outbound_send_residual_data = []

    def init_connect(self):
        self.set_inbound_protocol('Socks5', 'HttpProxy', server=True)
        self.set_outbound_protocol(self.config.protocol, server=False)
        self.handle_dns(self.config.remote_addr)

    def handle_inbound_recv_reply(self, reply):
        sendforward = reply.sendforward

        if reply.cmd == b'ADDR' and sendforward is not None:
            # maybe contains other data
            if type(sendforward) is list:
                addr = sendforward[0]
                other_data = b''.join(sendforward[1:])
                return [self.create_first_data(addr), other_data]
            else:
                addr = sendforward
                return self.create_first_data(addr)

        if sendforward:
            return sendforward

        return None

    def pre_outbound_send_data(self, data):
        data = self.encryptor.encrypt(data)

        return data

    def handle_outbound_send_reply(self, reply):
        sendforward = reply.sendforward

        if reply.cmd == b'WAIT' and sendforward is not None:
            self.outbound_send_residual_data.append(sendforward)
            return None

        if sendforward:
            return sendforward

        return None

    def pre_outbound_recv_reply(self, reply):
        reply.sendforward = self.encryptor.decrypt(reply.sendforward)

        return reply

    def handle_outbound_recv_reply(self, reply):
        if reply.cmd == b'DONE':
            for data in self.outbound_send_residual_data:
                self.to_sender_queue.put_nowait(data)

        if reply.sendforward:
            return reply.sendforward

        return None

    def create_first_data(self, addr):
        return b'\x03' + struct.pack('!B', len(addr[0])) + addr[
            0].encode() + struct.pack('!H', addr[1])


class ClientUdpProtocol(UdpProtocol):

    def __init__(self, *args):
        super().__init__(*args)

    def pre_to_sender_data(self, data):
        # connecting address is server address
        connect_addr = self.config.remote_addr

        if data[2] != 0:
            logging.warning('frag is not 0.Close udp transport!')
            self.transport.close()
            return False
        else:
            # remove socks5 header
            data = data[3:]
        # check authenticity
        results = ClientUdpProtocol.get_addr_from_data(data)
        if not results:
            return False

        # encrypt
        key, iv, m = cryptor.gen_key_iv(self.config.password, self.config.method)
        data = cryptor.encrypt_all_m(key, iv, m, self.config.method, data, None)

        return data, connect_addr

    def pre_to_local_data(self, data):
        data, key, iv = cryptor.decrypt_all(self.config.password, self.config.method, data, None)
        return b'\x00\x00\x00' + data

    @classmethod
    def get_addr_from_data(cls, data):
        atyp = data[0]
        try:
            if atyp == 1:
                addr = socket.inet_ntop(socket.AF_INET, data[1:5]), struct.unpack('!H', data[5:7])[0]
                data = data[7:]

            elif atyp == 3:
                addr_len = data[1]
                addr = data[2:2 + addr_len].decode(), struct.unpack('!H', data[2 + addr_len:])[0]
                data = data[2 + addr_len + 2:]

            elif atyp == 4:
                addr = socket.inet_ntop(socket.AF_INET6, data[1:17]), struct.unpack('!H', data[17:19])[0]
                data = data[19:]

            else:
                logging.warning('address type not supported,(not IPV4,HOSTNAME,IPV6)')
                return False
        except Exception as e:
            logging.error('getting addr data face error: %s' % e)
            return False

        return data, addr
