# coding=utf-8
import sys

sys.path.append('../')
from common import Reply


class plain(object):
    def __init__(self, server=True):
        self.server = server
        self.stage = 0
        self.info = {0: 'handling data transfer free'}
        self.server_info = None

    def hanle_server_recv(self, data):
        return Reply(None, None, data)

    def handle_server_send(self, data):
        return Reply(None, None, data)

    def handle_client_send(self, data):
        return Reply(None, None, data)

    def handle_client_recv(self, data):
        return Reply(None, None, data)

    def set_server_info(self, server_info):
        self.server_info = server_info

    def __str__(self):
        return 'plain'
