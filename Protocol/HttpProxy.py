# coding=utf-8
# handle http proxy protocol
import sys

sys.path.append('../')
from common import Reply


class HttpProxy(object):
    def __init__(self, server=True):
        self.server = True
        self.stage = 1 if not self.server else 4
        self.info = {4: 'server receiving requests from local',
                     5: 'server sending back reply',
                     0: 'handling data transfer free'
                     }
        self._addr = None

    def handle_server_recv(self, data):
        # server receiving requests from local
        if self.stage == 4:
            self.stage = 5
            return self.stage4_receive_requests(data)

        # handling data transfer free
        elif self.stage == 0:
            self.stage = 0
            return Reply(None, False, data)

        else:
            return False

    def handle_server_send(self, data):
        # server sending back reply
        if self.stage == 5:
            if data is not None:
                print('data is not None in http proxy send 1')
            self.stage = 0
            return Reply(None, False, b'HTTP/1.1 200 Connection Established\r\n\r\n')

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

    def stage4_receive_requests(self, data):
        # CONNECT
        if data[0:7] == b'CONNECT':
            hostname, port = data.decode().split(' ')[1].split(':')
            self._addr = hostname, int(port)
            return Reply(b'ADDR', True, self._addr)
        # GET/POST/HEAD
        else:
            hostname_port = None
            for line in data.decode().split('\r\n'):
                if line.startswith('Host:'):
                    hostname_port = line.split(' ')[1].split(':')
                    break
            if hostname_port is None:
                print('HTTP GET/POST/......    handling wrong!')
                print(data)
                return False
            if len(hostname_port) > 1:
                hostname, port = hostname_port[0], int(hostname_port[1])
            else:
                hostname = hostname_port[0]
                port = 80
            self._addr = hostname, port
            self.stage = 0

            return Reply(b'ADDR', False, [self._addr, data])

    @classmethod
    def check(cls, data):
        if data[0:7] == b'CONNECT':
            return True
        elif data[0:3] == b'GET':
            return True
        elif data[0:4] == b'POST':
            return True
        elif data[0:4] == b'HEAD':
            return True
        elif data[0:7] == b'OPTIONS':
            return True
        elif data[0:3] == b'PUT':
            return True
        elif data[0:6] == b'DELETE':
            return True
        else:
            return False

    def set_server_info(self, server_info):
        self.server_info = server_info

    def __str__(self):
        return 'HttpProxy'
