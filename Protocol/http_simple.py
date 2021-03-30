# coding=utf-8
import binascii
import datetime
import random
import sys

sys.path.append('../')
from common import Reply


class http_simple(object):
    def __init__(self, server=True):
        self.server = server
        self.stage = 1 if not self.server else 4
        self.info = {1: 'client sending http requests',
                     2: "client receiving server's response",
                     4: "server receiving client's requests",
                     5: 'server sending back response',
                     0: 'handling data transfer free'
                     }
        self.user_agent = [
            b"Mozilla/5.0 (Windows NT 6.3; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0",
            b"Mozilla/5.0 (Windows NT 6.3; WOW64; rv:40.0) Gecko/20100101 Firefox/44.0",
            b"Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
            b"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.11 (KHTML, like Gecko) Ubuntu/11.10 Chromium/27.0.1453.93 Chrome/27.0.1453.93 Safari/537.36",
            b"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:35.0) Gecko/20100101 Firefox/35.0",
            b"Mozilla/5.0 (compatible; WOW64; MSIE 10.0; Windows NT 6.2)",
            b"Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27",
            b"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.3; Trident/7.0; .NET4.0E; .NET4.0C)",
            b"Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko",
            b"Mozilla/5.0 (Linux; Android 4.4; Nexus 5 Build/BuildID) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/30.0.0.0 Mobile Safari/537.36",
            b"Mozilla/5.0 (iPad; CPU OS 5_0 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9A334 Safari/7534.48.3",
            b"Mozilla/5.0 (iPhone; CPU iPhone OS 5_0 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9A334 Safari/7534.48.3"
        ]

    def handle_client_send(self, data):
        # client sending http requests
        if self.stage == 1:
            self.stage = 2
            return self.stage1_send_requests(data)

        elif self.stage == 2:
            return Reply(b'WAIT', False, data)

        # handling data transfer free
        elif self.stage == 0:
            self.stage = 0
            return Reply(None, False, data)

        else:
            print('client send stage false', self.stage)
            return False

    def handle_client_recv(self, data):
        # client receiving server's response
        if self.stage == 2:
            self.stage = 0
            return Reply(b'DONE', False, None)

        # handling data transfer free
        elif self.stage == 0:
            self.stage = 0
            return Reply(None, False, data)

        else:
            print('client recv stage false', self.stage)
            return False

    def handle_server_recv(self, data):
        # server receiving client's requests
        if self.stage == 4:
            self.stage = 5
            return self.stage4_recv_requests(data)

        elif self.stage == 5:
            return Reply(b'WAIT', False, data)

        # handling data transfer free
        elif self.stage == 0:
            self.stage = 0
            return Reply(None, False, data)

        else:
            print('server recv stage false', self.stage)
            return False

    def handle_server_send(self, data):
        # server sending back response
        if self.stage == 5:
            self.stage = 0
            return self.stage5_send_response(data)

        # handling data transfer free
        elif self.stage == 0:
            self.stage = 0
            return Reply(None, False, data)

        else:
            print('server send stage false', self.stage)
            return False

    def stage1_send_requests(self, data):
        headdata = data
        port = b''
        if self.server_info['port'] != 80:
            port = b':' + str(self.server_info['port']).encode()
        hosts = self.server_info["protocol_param"] or self.server_info['server_address']
        pos = hosts.find('#')
        body = b''
        if pos >= 0:
            body = hosts[pos + 1:].replace('\n', '\r\n').replace('\\n', '\r\n')
            hosts = hosts[:pos]
        host = random.choice(hosts.split(','))
        http_head = b'GET /' + self.encode_head(headdata) + b' HTTP/1.1\r\n'
        http_head += b'Host: ' + host.encode() + port + b'\r\n'
        if body:
            http_head += body + b'\r\n\r\n'
        else:
            http_head += b"User-Agent: " + random.choice(self.user_agent) + b"\r\n"
            http_head += b"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n" \
                         b"Accept-Language: en-US,en;q=0.8\r\n" \
                         b"Accept-Encoding: gzip, deflate\r\n" \
                         b"DNT: 1\r\n" \
                         b"Connection: keep-alive\r\n\r\n"

        return Reply(None, False, http_head)

    def stage4_recv_requests(self, data):

        if b'\r\n\r\n' not in data:
            return False
        addr = self.get_data_from_http_header(data)

        host = self.get_host_from_http_header(data)
        other_data = self.get_other_data(data)
        if host and self.server_info["protocol_param"] is not '':
            pos = host.find(b':')
            if pos >= 0:
                host = host[:pos]
            hosts = self.server_info["protocol_param"].split(',')
            if host not in hosts:
                return False
        if len(addr) < 4:
            return False
        if len(addr) >= 13:
            if other_data is not None:
                addr = [addr, other_data]
            return Reply(b'ADDR', True, addr)
        return False

    def stage5_send_response(self, data):
        if data is not None:
            raise ValueError("server send's accepted data must be None")
        now = datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT').encode()
        sendforward = b'HTTP/1.1 200 OK\r\n' \
                      b'Connection: keep-alive\r\n' \
                      b'Content-Encoding: gzip\r\n' \
                      b'Content-Type: text/html\r\n' \
                      b'Date: ' + now + b'\r\n' \
                                        b'Server: nginx\r\n' \
                                        b'Vary: Accept - Encoding\r\n\r\n'

        return Reply(None, False, sendforward)

    def set_server_info(self, server_info):
        self.server_info = server_info

    def encode_head(self, data):
        hexstr = binascii.hexlify(data)
        chs = [b'%' + hexstr[i:i + 2] for i in range(0, len(hexstr), 2)]
        return b''.join(chs)

    # b'%61%62%63%64%65%65%66'
    # b'abcdeef'
    def get_data_from_http_header(self, data):

        lines = data.split(b'\r\n')
        if lines and len(lines) > 1:
            hex_items = lines[0][5:].split(b' ')[0].split(b'%')
            ret_buf = b''
            if hex_items and len(hex_items) > 1:
                for index in range(1, len(hex_items)):
                    if len(hex_items[index]) < 2:
                        ret_buf += binascii.unhexlify('0', hex_items[index])
                        break
                    elif len(hex_items[index]) > 2:
                        ret_buf += binascii.unhexlify(hex_items[index][:2])
                        break
                    else:
                        ret_buf += binascii.unhexlify(hex_items[index])
                return ret_buf
            return False

    def get_host_from_http_header(self, data):
        lines = data.split(b'\r\n')
        if lines and len(lines) > 1:
            for line in lines:
                if line.startswith(b'Host: '):
                    return line[6:].decode()

    def get_other_data(self, data):
        pos = data.find(b'\r\n\r\n')
        if len(data[pos:]) > 4:
            pos += 4
            return data[pos:]
        else:
            return None

    def __str__(self):
        return 'http_simple'
