# coding=utf-8


import socket
import struct

import cryptor
from base import TcpProtocol, UdpProtocol
from client import ClientUdpProtocol
from common import to_bytes, to_str


class ServerProtocol(TcpProtocol):
    def __init__(self, *args):
        super().__init__(*args)

    def init_connect(self):
        self.set_inbound_protocol(self.config.protocol, server=True)
        self.set_outbound_protocol('plain', server=False)

    def pre_inbound_recv_reply(self, reply):
        if type(reply.sendforward) is list:
            reply.sendforward = [self.encryptor.decrypt(i) for i in reply.sendforward]
            return reply

        reply.sendforward = self.encryptor.decrypt(reply.sendforward)

        return reply

    def handle_inbound_recv_reply(self, reply):
        # handle the first data to send
        sendforward = reply.sendforward

        if reply.cmd == b'ADDR' and sendforward:
            addr = sendforward
            other_data = None
            if type(sendforward) is list:
                addr = sendforward[0]
                other_data = sendforward[1]

            addr = self.get_addr_from_first_data(addr)
            if addr is None:
                self.transport.close()
                return None
            else:
                self.handle_dns(addr)
                if other_data is not None:
                    return other_data
                return None

        if sendforward:
            return sendforward

        return None

    def pre_inbound_send_data(self, data):
        data = self.encryptor.encrypt(data)

        return data

    def get_addr_from_first_data(self, data):

        try:
            if data[0] != 3:
                return None
            addr_len = data[1]
            if len(data) > addr_len + 4:
                other_data = data[2 + addr_len + 2:]
                print('find other data other then first addr data!')
                print(other_data)

            addr = data[2:2 + addr_len].decode(), struct.unpack('!H', data[2 + addr_len:2 + addr_len + 2])[0]
            return addr
        except Exception as e:
            print(e)
            print('handle addr failed,password or method is wrong!')
            return None


class ServerUdpProtocol(UdpProtocol):
    def __init__(self, *args):
        super().__init__(*args)

    def pre_to_sender_data(self, data):
        # decrypt
        data, key, iv = cryptor.decrypt_all(self.config.password, self.config.method, data, None)

        # check authenticity
        # get connecting address and raw data
        results = ClientUdpProtocol.get_addr_from_data(data)
        if not results:
            return False
        data, connect_addr = results[0], results[1]

        return data, connect_addr

    def pre_to_local_data(self, data):
        addr = self.pack_addr(self.sender.addr[0])
        data = addr + struct.pack('!H', self.sender.addr[1]) + data
        response = cryptor.encrypt_all(self.config.password, self.config.method, data, None)
        return response

    @staticmethod
    def pack_addr(address):
        address_str = to_str(address)
        address = to_bytes(address)
        for family in (socket.AF_INET, socket.AF_INET6):
            try:
                r = socket.inet_pton(family, address_str)
                if family == socket.AF_INET6:
                    return b'\x04' + r
                else:
                    return b'\x01' + r
            except (TypeError, ValueError, OSError, IOError):
                pass
        if len(address) > 255:
            address = address[:255]  # TODO
        return b'\x03' + struct.pack('!B', len(address)) + address
