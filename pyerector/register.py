#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

__all__ = [
    'Register', 'registry',
]

class Register(object):
    def __init__(self):
        self.map = {}
        self._cache = {}
    def __repr__(self):
        return repr(self.map)
    def append(self, name, cls):
        self.map[name] = cls
    def __contains__(self, name):
        return name in self.map
    def __getitem__(self, name):
        return self.map[name]
    def __setitem__(self, name, value):
        self.map[name] = value
    def __delitem__(self, name):
        del self.map[name]
    def __len__(self):
        return len(self.map)
    def __iter__(self):
        return iter(self.map)
    def get(self, name):
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

