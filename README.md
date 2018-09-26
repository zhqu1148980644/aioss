# aioss
ss proxy forked from [shadowsocks](https://github.com/shadowsocks/shadowsocks/tree/master)
Rewrited using asyncio library(python 3.5+)

## Requirements:
python(3.5+),uvloop(only in server)
## Features:
### Extensible:
Inbound and outbound protocol wre abstracted from SOCKS5,HTTP(obfs)  in ss
Inspired by [hyper-h2](https://hyper-h2.readthedocs.io/en/stable)
### Fast:
using [uvloop](https://github.com/MagicStack/uvloop) in server 

- TCP/UDP support
- HTTP proxy support
- simple obfs support

## Usage:
Not fully completed.If you insist on,use the command:
	cd test
	python test_server.py -c server_config_normal.json

	cd test
	python test_client.py -c client_config_normal.json
