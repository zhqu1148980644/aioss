# coding=utf-8
# distribute request to different protocol handler
from Protocol import Socks5, HttpProxy, plain, http_simple, http_post

PROTOCOL_MAPS = {
    'Socks5': Socks5.Socks5,
    'HttpProxy': HttpProxy.HttpProxy,
    'plain': plain.plain,
    'http_simple': http_simple.http_simple,
    'http_post': http_post.http_post,
}


class Protocol(object):
    def __init__(self, *protocols, server=False, config):
        self.config = config
        self.server = server
        self.protocols = [PROTOCOL_MAPS[protocol] for protocol in protocols if len(protocols) > 1]
        self.protocol = PROTOCOL_MAPS[protocols[0]](self.server) if len(protocols) == 1 else None
        self.set_server_info()
        self.first_data = None

    # check if received data fit any protocol
    def check(self, data):
        if data is None:
            print('receiving               none data')
        self.first_data = data
        if len(self.protocols) > 1:
            for protocol in self.protocols:
                fit_protocol = protocol.check(data)
                if fit_protocol:
                    self.protocol = protocol(server=self.server)
                    # print('set protocol ', self.protocol)
                    return
            if self.protocol is None:
                print('handling data not mathch any protocol', data)
        else:
            raise ValueError

    def handle_server_recv(self, data):
        if self.protocol is None:
            self.check(data)
        return self.protocol.handle_server_recv(data)

    def handle_server_send(self, data):
        return self.protocol.handle_server_send(data)

    def handle_client_send(self, data):
        return self.protocol.handle_client_send(data)

    def handle_client_recv(self, data):
        return self.protocol.handle_client_recv(data)

    def set_server_info(self):
        if self.protocol is not None:
            self.protocol.set_server_info(self.config)
