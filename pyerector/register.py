#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import threading

__all__ = [
    'Register', 'registry',
]


class Register(object):
    def __init__(self):
        self.lock = threading.RLock()
        self.map = {}
        self._cache = {}

    def __repr__(self):
        with self.lock:
            return repr(self.map)

    def append(self, name, cls):
        with self.lock:
            self.map[name] = cls

    def __contains__(self, name):
        with self.lock:
            return name in self.map

    def __getitem__(self, name):
        with self.lock:
            return self.map[name]

    def __setitem__(self, name, value):
        with self.lock:
            self.map[name] = value

    def __delitem__(self, name):
        with self.lock:
            del self.map[name]

    def __len__(self):
        with self.lock:
            return len(self.map)

    def __iter__(self):
        with self.lock:
            return iter(self.map)

    def get(self, name):
        with self.lock:
            cls = self[name]
            if cls in self._cache:
                return self._cache[cls]
            else:
                c = self._cache[cls] = {}
                for name in self:
                    kls = self[name]
                    if issubclass(kls, cls) and cls is not kls:
                        c[name] = kls
                return c

registry = Register()
