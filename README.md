# aioss
Ss proxy rewrited using asyncio library(python 3.5+). 
You can find the official version in  [shadowsocks](https://github.com/shadowsocks/shadowsocks/tree/master). 
### Requirements
- python(3.5+)
- uvloop(only in server)
### Features
#### Fast
Using superfast [uvloop](https://github.com/MagicStack/uvloop) in server.
#### Extensible
Inbound and outbound protocol wre abstracted from SOCKS5,HTTP(obfs)  in ss.
Inspired by [hyper-h2](https://hyper-h2.readthedocs.io/en/stable).
#### Compatible
You can use any ss/ssr client(pc/android/mac/linux) to connect server in which you installed aioss.
#### Supports
- TCP/UDP support.
- HTTP proxy support.
- simple obfs support.
### Usage
Not fully completed.If you insist on,use the command:
#### server
	cd test
	python test_server.py -c server_config_normal.json
#### client
	cd test
	python test_client.py -c client_config_normal.json
