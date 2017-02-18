#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.
"""A thread-safe mapping object with a single instance, register."""

import threading

__all__ = [
    'registry',
]


class Register(object):
    """Emulate a dicutionary, but thread-safe(?)."""
    def __init__(self):
        self.lock = threading.RLock()
        self.map = {}
        self._cache = {}

    def __repr__(self):
        with self.lock:
            return repr(self.map)

    def append(self, name, cls):
        """Add a new mapping."""
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
        """Return a dict of all items of the same type as the one
being given.  For example, if "All" is given, then return a dict of all
Target subclasses."""
        with self.lock:
            cls = self[name]
            if cls in self._cache:
                return self._cache[cls]
            else:
                # build up the cache
                clscache = self._cache[cls] = {}
                for name in self:
                    kls = self[name]
                    if issubclass(kls, cls) and cls is not kls:
                        clscache[name] = kls
                return clscache

# pylint: disable=invalid-name
registry = Register()
