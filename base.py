# coding=utf-8
"""
base
    TcpProtocol
sender
    SenderProtocol
client
    ClientServer(BaseProtocl)
server
    ServerServer(TcpProtocol)
protocol
    Protocol
    Socks5
    HttpProxy
    plain
    http_simple
    http_post
    https
config
    Config
    UserConfig
cache
    class dns_cache
    class user_cache
crypto
    from shadowsocks

first send message to server:
socks5:    b'\x03\x0dwww.baidu.com\x01\xbb'         clould start with \x01 \x03  \x04

http:      b'\x03\x0dwww.baidu.com\x01\xbb'         always start with \x03
    CONNECT:
    GET/POST/...:
"""

import asyncio
import logging

from cryptor import Cryptor
from protocol import Protocol


# Basic TCP transfer class
class TcpProtocol(asyncio.Protocol):

    def __init__(self, loop, dns_cache, config_getter, server=False):
        self.server = server
        self.config_getter = config_getter
        self.dns_cache = dns_cache
        self.loop = loop

        self.transport = None
        self.sender = None

        self.config = None
        self.encryptor = None
        self.inbound_protocol = None
        self.outbound_protocol = None
        self.raw_addr = None
        self.resolved_addr = None

        self.dns_resolved = asyncio.Event()
        self.sender_created = asyncio.Event()

        self.to_sender_queue = asyncio.Queue()
        self.to_local_queue = asyncio.Queue()

    def connection_made(self, transport):
        self.transport = transport
        # print('connection from local,port:{}'.format(self.transport.get_extra_info('peername')[1]))
        # print('connection from client,port:{}'.format(self.transport.get_extra_info('peername')[1]))
        self.set_user_config()
        self.init_connect()
        self._task = asyncio.ensure_future(self.start_send())

    def data_received(self, data):
        self.data_from_local(data)

    def connection_lost(self, err):
        super().connection_lost(err)
        self.transport.close()
        self._task.cancel()

    def eof_received(self):
        super().eof_received()
        self.transport.close()
        self._task.cancel()

    def set_user_config(self):
        port = self.transport.get_extra_info('sockname')[1]
        self.config = self.config_getter(port)
        self.encryptor = Cryptor(*self.config.encryptor)

    # use handle_dns to create a sender
    # handle dns
    def handle_dns(self, addr):
        if not self.dns_cache.get(addr[0]):
            # print('hosname not in dns_cache,resolve dns')
            asyncio.ensure_future(self.resolve_dns(addr))
        else:
            # print('find hostname in dns_cache')
            if not self.dns_resolved.is_set():
                self.resolved_addr = self.dns_cache.get(addr[0]), addr[1]
                # print('find dns',self.resolved_addr)
                self.dns_resolved.set()
                asyncio.ensure_future(self.create_sender())

    async def resolve_dns(self, addr):
        try:
            self.raw_addr = addr
            addrinfo = await self.loop.getaddrinfo(*addr)
            self.resolved_addr = addrinfo[0][4]
            self.dns_cache[addr[0]] = self.resolved_addr[0]
            self.dns_resolved.set()
            await self.create_sender()
        except Exception as e:
            self.transport.close()
            print(e)

    async def create_sender(self):
        if not self.sender_created.is_set():
            try:
                tmp_addr = self.resolved_addr
                if tmp_addr is None:
                    self.transport.close()
                    raise ValueError
                _, self.sender = await self.loop.create_connection(lambda: SenderProtocol(self, self.loop), *tmp_addr)
                self.sender_created.set()
            except Exception as e:
                logging.warning('sender could not be created!')

    # data from local     >>>>>> inbound >>>>>>> outbound >>>>>>       data to sender
    #                                                 data from local
    def data_from_local(self, data):
        self._handle_inbound_recv(data)

    def _handle_inbound_recv(self, data):
        data = self.handle_inbound_recv(data)

        if data is not None:
            # data must be unencrypted data            inbound  >>>  outbound
            if type(data) is list:
                # if reply.sendforward's type is list,means we should send separately
                self._handle_outbound_send(data[0])
                self._handle_outbound_send(b''.join(data[1:]))
            else:
                self._handle_outbound_send(data)

    def handle_inbound_recv(self, data):
        reply = self.inbound_protocol.handle_server_recv(data)
        if not reply:
            print('indound recv returns reply uncorrectly!')
            return None

        # handle sendback
        if reply.sendback:
            self._handle_inbound_send(None)
            reply.sendback = False

        if reply.sendforward:
            reply = self.pre_inbound_recv_reply(reply)
        data = self.handle_inbound_recv_reply(reply)
        return data

    def _handle_outbound_send(self, data):
        data = self.handle_outbound_send(data)
        #                                         data to sender
        self.data_to_sender(data)

    def handle_outbound_send(self, data):
        if data is not None:
            data = self.pre_outbound_send_data(data)

        reply = self.outbound_protocol.handle_client_send(data)
        if not reply:
            print('outbound send  returns reply uncorrectly!')
            return None

        data = self.handle_outbound_send_reply(reply)
        return data

    #                                                 data to sender
    def data_to_sender(self, data):
        if data is not None:
            self.to_sender_queue.put_nowait(data)

    # data from sender     >>>>>> outbound >>>>>>> inbound >>>>>>       data to local
    #                                                 data from sender
    def data_from_sender(self, data):
        self._handle_outbound_recv(data)

    def _handle_outbound_recv(self, data):
        data = self.handle_outbound_recv(data)

        if data is not None:
            # data must be unencrypted data          outbound  >>>  inbound
            self._handle_inbound_send(data)

    def handle_outbound_recv(self, data):
        reply = self.outbound_protocol.handle_client_recv(data)
        if not reply:
            print('outbound recv stage not return reply correctly!')
            return None

        # handle sendback
        if reply.sendback:
            self._handle_outbound_send(None)
            reply.sendback = False

        if reply.sendforward:
            reply = self.pre_outbound_recv_reply(reply)

        data = self.handle_outbound_recv_reply(reply)
        return data

    def _handle_inbound_send(self, data):
        data = self.handle_inbound_send(data)
        #                                       data to local
        self.data_to_local(data)

    def handle_inbound_send(self, data):
        # None means handle protocol ,doesn't need encrypt
        if data is not None:
            data = self.pre_inbound_send_data(data)

        reply = self.inbound_protocol.handle_server_send(data)
        if not reply:
            print('indound send stage not return reply correctly!')
            return None

        data = self.handle_inbound_send_reply(reply)
        return data

    #                                                 data to local
    def data_to_local(self, data):
        if data is not None:
            self.to_local_queue.put_nowait(data)

    async def start_send(self):
        while True:
            data = await self.to_local_queue.get()
            self.transport.write(data)

    def set_inbound_protocol(self, *inbound_protocol, server=False):
        self.inbound_protocol = Protocol(*inbound_protocol, server=server, config=self.config.config)

    def set_outbound_protocol(self, *outbound_protocol, server=False):
        self.outbound_protocol = Protocol(*outbound_protocol, server=server, config=self.config.config)

    # ......................REWRITE YOUR OWN REPLY CONTROLLER.......................
    def init_connect(self):
        self.set_inbound_protocol('Socks5', 'HttpProxy', server=self.server)
        self.set_outbound_protocol('plain', server=self.server)

    def pre_inbound_recv_reply(self, reply):
        return reply

    def handle_inbound_recv_reply(self, reply):
        if reply.sendforward:
            return reply.sendforward

        return None

    def pre_outbound_send_data(self, data):
        return data

    def handle_outbound_send_reply(self, reply):
        if reply.sendforward:
            return reply.sendforward

        return None

    def pre_outbound_recv_reply(self, reply):
        return reply

    def handle_outbound_recv_reply(self, reply):
        if reply.sendforward:
            return reply.sendforward

        return None

    def pre_inbound_send_data(self, data):
        return data

    def handle_inbound_send_reply(self, reply):
        if reply.sendforward:
            return reply.sendforward

        return None


class SenderProtocol(asyncio.Protocol):
    def __init__(self, local_protocol, loop):

        super().__init__()
        self.loop = loop
        self.local_protocol = local_protocol
        self.config = self.local_protocol.config

    def connection_made(self, transport):
        self.transport = transport
        self._task = asyncio.ensure_future(self.start_send())

    def data_received(self, data):
        if not self.local_protocol.transport.is_closing():
            self.local_protocol.data_from_sender(data)

    def connection_lost(self, err):
        super().connection_lost(err)
        self.transport.close()
        self._task.cancel()

    def eof_received(self):
        super().eof_received()
        self.transport.close()
        self._task.cancel()

    async def start_send(self):
        while True:
            data = await self.local_protocol.to_sender_queue.get()
            self.transport.write(data)


class UdpProtocol(asyncio.DatagramProtocol):
    def __init__(self, loop, dns_cache, config_getter):
        super().__init__()
        self.loop = loop
        self.dns_cache = dns_cache
        self.config_getter = config_getter
        self.sender = None

        self.dns_resolved = asyncio.Event()
        self.sender_created = asyncio.Event()

        self.to_sender_queue = asyncio.Queue()

    def connection_made(self, transport):
        self.transport = transport
        self.set_user_config()

    def connection_lost(self, err):
        super().connection_lost(err)
        self.transport.close()

    def error_received(self, exc):
        super().error_received()
        self.transport.close()

    def set_user_config(self):
        port = self.transport.get_extra_info('sockname')[1]
        self.config = self.config_getter(port)

    def datagram_received(self, data, addr):
        self.addr = addr
        self.to_sender(data)

    def pre_to_sender_data(self, data):
        return data, addr

    def to_sender(self, data):
        result = self.pre_to_sender_data(data)
        if not result:
            return
        data, addr = result[0], result[1]
        self.handle_dns(addr)
        self.to_sender_queue.put_nowait(data)

    def pre_to_local_data(self, data):
        return data

    def to_local(self, data):
        data = self.pre_to_local_data(data)
        self.transport.sendto(data, self.addr)

    # use handle_dns to create a sender
    # handle dns
    def handle_dns(self, addr):
        if not self.dns_cache.get(addr[0]):
            # print('hosname not in dns_cache,resolve dns')
            asyncio.ensure_future(self.resolve_dns(addr))
        else:
            # print('find hostname in dns_cache')
            if not self.dns_resolved.is_set():
                self.resolved_addr = self.dns_cache.get(addr[0]), addr[1]
                # print('find dns',self.resolved_addr)
                self.dns_resolved.set()
                asyncio.ensure_future(self.create_sender())

    async def resolve_dns(self, addr):
        try:
            self.raw_addr = addr
            addrinfo = await self.loop.getaddrinfo(*addr)
            self.resolved_addr = addrinfo[0][4]
            self.dns_cache[addr[0]] = self.resolved_addr[0]
            self.dns_resolved.set()
            await self.create_sender()
        except Exception as e:
            print(addr)
            self.transport.close()
            print(e)

    async def create_sender(self):
        if self.sender_created.is_set():
            return
        try:
            tmp_addr = self.resolved_addr
            if tmp_addr is None:
                self.transport.close()
                raise ValueError
            _, self.sender = await self.loop.create_datagram_endpoint(lambda: UdpSenderProtocol(self, self.loop),
                                                                      remote_addr=tmp_addr)
            self.sender_created.set()
        except Exception as e:
            print('sender could not create,time out!')
            print(e)


class UdpSenderProtocol(asyncio.DatagramProtocol):
    def __init__(self, local_protocol, loop):
        super().__init__()
        self.local_protocol = local_protocol
        self.loop = loop

    def connection_made(self, transport):
        self.transport = transport
        self.addr = self.transport.get_extra_info('peername')
        self._task = asyncio.ensure_future(self.start_send())

    def datagram_received(self, data, addr):
        self.addr = addr
        self.local_protocol.to_local(data)

    def connection_lost(self, err):
        super().connection_lost(err)
        self.transport.close()
        self._task.cancel()

    def error_received(self, exc):
        super().error_received()
        self.transport.close()
        self._task.cancel()

    async def start_send(self):
        while True:
            data = await self.local_protocol.to_sender_queue.get()
            self.transport.sendto(data, self.addr)
