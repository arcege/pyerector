#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import threading
from .exception import Abort, Error

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
        # this works because at _this_ time, the new thread has not been
        # created, so currentThread will still have the parent stack
        parentstack = get_current_stack()
        self.stack = ExecStack(parentstack)
        self.exception = None
    def run(self):
        import logging, sys
        logger = logging.getLogger('pyerector.execute')
        try:
            super(PyThread, self).run()
        except Error:
            t, e, tb = sys.exc_info()
            logger.exception('Exception in %s', self.name)
            self.exception = e
            raise Abort

def initialize_threading():
    curthread = threading.currentThread()
    assert curthread.name == 'MainThread'
    if not hasattr(curthread, 'stack'):
        curthread.stack = ExecStack()

