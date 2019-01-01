import asyncio
import sys

sys.path.append(r'../')
from server import ServerProtocol, ServerUdpProtocol
from cache import DnsCache
from config import Config

# in unix,test in windows
# import uvloop
# asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
# if sys.platform == 'win32':
#
#     l = asyncio.ProactorEventLoop()
#     asyncio.set_event_loop(l)
# else:
#     import uvloop
#     asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
dns = DnsCache()
loop = asyncio.get_event_loop()

config_getter = Config(server=True)
servers = []

for key, value in config_getter.full_config['users'].items():
    port = value['port']
    coro = loop.create_server(lambda: ServerProtocol(loop, dns, config_getter, True), '127.0.0.1', port)
    server = loop.run_until_complete(coro)
    udp = asyncio.ensure_future(loop.create_datagram_endpoint(lambda: ServerUdpProtocol(loop, dns, config_getter),
                                                              local_addr=('127.0.0.1', port)))
    servers.append(server)
print("server created,waiting for local client's request")
print(servers)
try:
    loop.run_forever()
except KeyboardInterrupt as e:
    print('all tasks cancelled')
    print(asyncio.gather(asyncio.Task.all_tasks()).cancel())
server.close()
loop.run_until_complete(asyncio.wait(servers))
loop.close()
