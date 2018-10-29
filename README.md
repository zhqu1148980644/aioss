# aioss
shadowsocks using asyncio

## A rubbish wheel,not fully completed.

## Requirement
- python 3.5+
- uvloop (Optional,makes asyncio faster 2-3x)
- libsodium
- openssl

## Usage
#### server
```python
cd test
python test_server.py -c server_config_normal.json
```
#### client
```python
cd test
python test_client.py -c client_config_normal.json
```

## Features
- Extensible
- Fast
- HTTP proxy suport
- UDP support
- simple HTTP obfs support

