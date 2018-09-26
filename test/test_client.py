import asyncio
import sys

sys.path.append(r'../')
from client import ClientProtocol, ClientUdpProtocol
from cache import dns_cache
from config import Config

# in unix,test in windos
# import uvloop
# asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# if sys.platform == 'win32':
#     l = asyncio.ProactorEventLoop()
#     asyncio.set_event_loop(l)
# else:
#     import uvloop
#
#     asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

dns = dns_cache()
loop = asyncio.get_event_loop()
config_getter = Config()
user_config = config_getter('127.0.0.1')
local_addr = user_config.config['local_address']
local_port = user_config.config['local_port']
coro = loop.create_server(lambda: ClientProtocol(loop, dns, config_getter, False), local_addr, local_port)
server = loop.run_until_complete(coro)
udp = asyncio.ensure_future(loop.create_datagram_endpoint(lambda: ClientUdpProtocol(loop, dns, config_getter),
                                                          local_addr=(local_addr, local_port)))
print("server created,waiting for local client's request")
try:
    loop.run_forever()
except KeyboardInterrupt as e:
    print('all tasks cancelled')
    print(asyncio.gather(asyncio.Task.all_tasks()).cancel())
server.close()
loop.run_until_complete(server.wait_closed())
loop.close()
