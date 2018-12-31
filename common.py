# coding=utf-8
import logging
from logging.handlers import RotatingFileHandler


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
    if bytes != str:
        if type(s) == bytes:
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
file_handler = RotatingFileHandler('aioss.txt', maxBytes=5 * 1024, backupCount=3)
file_handler.setLevel(logging.WARNING)
file_handler.setFormatter(formatter)

# formatter = logging.Formatter('%(levelname)s-%(asctime)s - %(module)s-%(funcName)s-%(lineno)s - %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)
