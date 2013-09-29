#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import threading

__all__  = [
    'get_current_stack',
    'ExecStack',
    'PyThread',
]

class ExecStack(object):
    def __init__(self, parent=None):
        self.stack = []
        self.pos = None
        self.parent = parent
        self.lock = threading.RLock()
    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.stack)
    def push(self, frame):
        with self.lock:
            self.stack.append(frame)
    def pop(self):
        with self.lock:
            return self.stack.pop()
    def __len__(self):
        with self.lock:
            if isinstance(self.parent, ExecStack):
                parlen = len(self.parent)
            else:
                parlen = 0
            return parlen + len(self.stack)
    def __iter__(self):
        from itertools import chain
        with self.lock:
            if self.parent is not None:
                return chain(self.parent, self.stack)
            else:
                return iter(self.stack)
    def extract(self):
        lines = []
        indent = 0
        with self.lock:
            for item in self:
                lines.append(
                    '%s%s\n' % ('  ' * indent, item.__class__.__name__)
                )
                indent += 1
        return lines

def get_current_stack():
    return threading.currentThread().stack

class PyThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        from .base import Target, Task
        super(PyThread, self).__init__(*args, **kwargs)
        if 'parent' in kwargs:
            self.stack = ExecStack(kwargs['parent'])
        else:
            self.stack = ExecStack()

def initialize_threading():
    curthread = threading.currentThread()
    assert curthread.name == 'MainThread'
    if not hasattr(curthread, 'stack'):
        curthread.stack = ExecStack()

