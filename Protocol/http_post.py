# coding=utf-8
import random
import sys

sys.path.append('../')
from common import Reply
from .http_simple import http_simple


class http_post(http_simple):
    def __init__(self, server=True):
        super().__init__(server=server)

    def stage1_send_requests(self, data):
        headdata = data
        port = b''
        if self.server_info['port'] != 80:
            port = b':' + str(self.server_info['port']).encode()
        body = None
        hosts = (self.server_info['protocol_param'] or self.server_info['port'])
        pos = hosts.find("#")
        if pos >= 0:
            body = hosts[pos + 1:].replace("\\n", "\r\n")
            hosts = hosts[:pos]
        hosts = hosts.split(',')
        host = random.choice(hosts)
        http_head = b"POST /" + self.encode_head(headdata) + b" HTTP/1.1\r\n"
        http_head += b"Host: " + to_bytes(host) + port + b"\r\n"
        if body:
            http_head += body + "\r\n\r\n"
        else:
            http_head += b"User-Agent: " + random.choice(self.user_agent) + b"\r\n"
            http_head += b"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\nAccept-Language: en-US,en;q=0.8\r\nAccept-Encoding: gzip, deflate\r\n"
            http_head += b"Content-Type: multipart/form-data; boundary=" + b"\r\nDNT: 1\r\n"
            http_head += b"Connection: keep-alive\r\n\r\n"
        return Reply(None, None, http_head)

    def __str__(self):
        return 'http_post'
