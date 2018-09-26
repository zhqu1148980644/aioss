# coding=utf-8
import collections


class dns_cache(collections.UserDict):
    def __init__(self):
        self._data = {}

    def __getitem__(self, item):
        return self._data[item]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __contains__(self, item):
        return item in self._data

    def __len__(self):
        return len(self._data)

# class config_cache(collections.UserDict):
