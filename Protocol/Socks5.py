# coding=utf-8
# handle socks5 proxy protocol
#
#                   +----+----------+----------+
#                   |VER | NMETHODS | METHODS  |
#                   +----+----------+----------+
#                   | 1  |    1     | 1 to 255 |
#                   +----+----------+----------+
#
#
#
#                         +----+--------+
#                         |VER | METHOD |
#                         +----+--------+
#                         | 1  |   1    |
#                         +----+--------+
#
#
#         +----+-----+-------+------+----------+----------+
#         |VER | CMD |  RSV  | ATYP | DST.ADDR | DST.PORT |
#         +----+-----+-------+------+----------+----------+
#         | 1  |  1  | X'00' |  1   | Variable |    2     |
#         +----+-----+-------+------+----------+----------+
#
#
#
#         +----+-----+-------+------+----------+----------+
#         |VER | REP |  RSV  | ATYP | BND.ADDR | BND.PORT |
#         +----+-----+-------+------+----------+----------+
#         | 1  |  1  | X'00' |  1   | Variable |    2     |
#         +----+-----+-------+------+----------+----------+
#
#
#
#       +----+------+------+----------+----------+----------+
#       |RSV | FRAG | ATYP | DST.ADDR | DST.PORT |   DATA   |
#       +----+------+------+----------+----------+----------+
#       | 2  |  1   |  1   | Variable |    2     | Variable |
#       +----+------+------+----------+----------+----------+
#
#
#
#
#
#
#
import socket
import struct
import sys

sys.path.append('../')
from common import Reply


class Socks5(object):

    def __init__(self, server=True):
        self.server = server
        self.stage = 1 if not self.server else 4
        self.info = {4: 'server receiving select-methods requests',
                     5: 'server sending back selected method',
                     6: 'server receiving connect-address requests',
                     7: 'server sending back connect-address reply',
                     0: 'handling data transfer free'
                     }
        self._addr = None
        self.udp_associate = False

    def handle_server_recv(self, data):
        # server receiving select-methods requests
        if self.stage == 4:
            self.stage = 5
            return self.stage4_select_methods(data)

        # server receiving connect-address requests
        elif self.stage == 6:
            self.stage = 7
            return self.stage6_receive_requests(data)

        # handling data transfer free
        elif self.stage == 0:
            self.stage = 0
            return Reply(None, False, data)

        else:
            return False

    def handle_server_send(self, data):
        # server sending back selected method
        if self.stage == 5:
            if data is not None:
                print('data is not None in socks5 send 5')
            self.stage = 6
            return Reply(None, False, b'\x05\x00')

        # server sending back connect-address reply
        elif self.stage == 7:
            if data is not None:
                print('data is not None in socks5 send 7')
            self.stage = 0
            # UDP ASSOCIATE
            if self.udp_associate:
                bind_addr = socket.inet_pton(socket.AF_INET, self.server_info['local_address'])
                bind_port = struct.pack('!H', int(self.server_info['local_port']))
                return Reply(None, False, b'\x05\x00\x00\x01' + bind_addr + bind_port)

            else:
                return Reply(None, False, b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')

        # handling data transfer free
        elif self.stage == 0:
            self.stage = 0
            return Reply(None, False, data)

        else:
            return False

    def handle_client_send(self, data):
        return data

    def handle_client_recv(self, data):
        return data

    def stage4_select_methods(self, data):

        try:
            methods = [i for i in data[2:2 + 6]]
        except Exception as e:
            print(e)
            methods = []
        finally:
            if 0 in methods:
                return Reply(None, True, None)
            else:
                print('client does not support none-authorization')
                return False

    def stage6_receive_requests(self, data):
        ver, cmd, rsv, atyp = struct.unpack('!BBBB', data[0:4])
        self._addr = self.get_addr(atyp, data)

        # CONNECT
        if cmd == 1:
            return Reply(b'ADDR', True, self._addr)

        # BIND
        elif cmd == 2:
            return False

        # UDP ASSOCIATE
        elif cmd == 3:
            self.udp_associate = True
            return Reply(b'UDP', True, None)

        else:
            return False

    # handling client request hostname_bytes ,and return hostname and port
    @staticmethod
    def get_addr(atyp, data):
        # IPV4 address
        if atyp == 1:
            # addr = '.'.join(list(map(lambda x: str(x), struct.unpack('!BBBB', data[4:8]))))
            addr = socket.inet_ntop(socket.AF_INET, data[4:8])
            port = struct.unpack('!HH', data[8:10])[0]

        # HOSTNAME
        elif atyp == 3:
            addr = data[5:-2].decode()
            port = struct.unpack('!H', data[-2:])[0]

        # IPV6 address
        elif atyp == 4:
            # addr = ':'.join(list(map(lambda x: str(hex(x)[2:]), struct.unpack('!HHHHHHHH', data[4:20]))))
            addr = socket.inet_ntop(socket.AF_INET6, data[4:20])
            port = struct.unpack('!HH', data[20:22])[0]
        else:
            return False

        return addr, port

    @classmethod
    def check(cls, data):
        if data[0] == 5:
            return True
        else:
            return False

    def set_server_info(self, server_info):
        self.server_info = server_info

    def __str__(self):
        return 'Socks5'
