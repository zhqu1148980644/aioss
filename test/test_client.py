import asyncio
import sys

sys.path.append(r'../')
from client import ClientProtocol, ClientUdpProtocol
from cache import DnsCache
from config import Config
from common import set_proxy

if sys.platform == 'win32':
    win_Loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(win_Loop)
else:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

dns = DnsCache()
loop = asyncio.get_event_loop()
config_getter = Config()
user_config = config_getter()
local_addr = user_config.config['local_address']
local_port = user_config.config['local_port']
if sys.platform == 'win32':
    set_proxy(1, local_addr + ':' + str(local_port))
coro = loop.create_server(lambda: ClientProtocol(loop, dns, config_getter, False), local_addr, local_port)
server = loop.run_until_complete(coro)
# udp = asyncio.ensure_future(loop.create_datagram_endpoint(lambda: ClientUdpProtocol(loop, dns, config_getter),
#                                                           local_addr=(local_addr, local_port)))
print("server created,waiting for local client's request")
try:
    loop.run_forever()
except KeyboardInterrupt as e:
    print('all tasks cancelled')
    print(asyncio.gather(asyncio.Task.all_tasks()).cancel())
    if sys.platform == 'win32':
        set_proxy(0, "127.0.0.1:1080")

server.close()
loop.run_until_complete(server.wait_closed())
loop.close()
