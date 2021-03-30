# coding=utf-8
import logging
import winreg
from logging.handlers import RotatingFileHandler

PROXY_PATH = r"Software/Microsoft/Windows/CurrentVersion/Internet Settings"
KEY_PROXYENABLE = "ProxyEnable"
KEY_PROXYSERVER = "ProxyServer"
KEY_PROXYOVERRIDE = "ProxyOverride"


def get_proxy_status():
    proxy = winreg.OpenKey(winreg.HKEY_CURRENT_USER, PROXY_PATH, 0, winreg.KEY_READ)
    enable = winreg.QueryValueEx(proxy, KEY_PROXYENABLE)
    addr = winreg.QueryValueEx(proxy, KEY_PROXYSERVER)
    ignore = winreg.QueryValueEx(proxy, KEY_PROXYOVERRIDE)
    winreg.CloseKey(proxy)

    return enable[0], addr[0], ignore[0]


def set_proxy(enable=1, addr="127.0.0.1:1080", ignore=""):
    try:
        proxy = winreg.OpenKey(winreg.HKEY_CURRENT_USER, PROXY_PATH, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(proxy, KEY_PROXYENABLE, 0, winreg.REG_DWORD, enable)
        winreg.SetValueEx(proxy, KEY_PROXYSERVER, 0, winreg.REG_SZ, addr)
        winreg.SetValueEx(proxy, KEY_PROXYOVERRIDE, 0, winreg.REG_SZ, ignore)
        winreg.CloseKey(proxy)
        return True
    except Exception as e:
        logging.exception("set proxy (%d %s %s) failed." % (enable, addr, ignore))
        return False


class Reply(object):
    def __init__(self, command, sendback, sendforward):
        self.cmd = command
        self.sendback = sendback
        self.sendforward = sendforward

    def __str__(self):
        return '{} {} {}'.format(self.cmd, self.sendback, self.sendforward)


def to_bytes(data):
    if type(data) is str:
        return data.encode()
    else:
        return data


def to_str(s):
    if bytes != str and type(s) == bytes:
        return s.decode('utf-8')
    return s


def compat_ord(s):
    if type(s) == int:
        return s
    return _ord(s)


def compat_chr(d):
    if bytes == str:
        return _chr(d)
    return bytes([d])


_ord = ord
_chr = chr
ord = compat_ord
chr = compat_chr

logger = logging.getLogger('BaseLogger')
logger.setLevel(level=logging.INFO)

formatter = logging.Formatter('%(levelname)s-%(asctime)s - %(module)s-%(funcName)s-%(lineno)s - %(message)s')
file_handler = RotatingFileHandler('aioss.log', maxBytes=5 * 1024, backupCount=3)
file_handler.setLevel(logging.WARNING)
file_handler.setFormatter(formatter)

# formatter = logging.Formatter('%(levelname)s-%(asctime)s - %(module)s-%(funcName)s-%(lineno)s - %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

if __name__ == "__main__":
    print(get_proxy_status())
    set_proxy(1, '255.255.255.1:2010', "127.0.123.4")
    assert get_proxy_status() == (1, '255.255.255.1:2010', "127.0.123.4")
    set_proxy(0, '127.0.0.1:1080', "")
    assert get_proxy_status() == (0, '127.0.0.1:1080', "")
