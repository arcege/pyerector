#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.
"""Implement an internal version of Python's frame stack, but for Initer
instances.  This allows for showing tracebacks of the targets and tasks,
not the underlying Python calls (which are often recursive calls to the
same Target.__call__ method).

The execution stack, ExecStack, can take a parent, supposedly another
thread which called this one.  Operations are based on that stack along
with the ancesters'.

Also defines a specialized version of threading.Thread which creates a
new execution stack based on the parent's.
"""

import threading
from .exception import Abort, Error
from .variables import V

__all__ = [
    'get_current_stack',
    'PyThread',
]


class ExecStack(object):
    """An execution stack, with reference to caller's execution stack.
Operations such as len(s) s[], iter() all access the ancester's stack(s)
before performing the operations here.

For example:
    s0 = ExecStack()
    s0.push('a')
    s0.push('b')
    s1 = ExecStack(s0)
    s1.push('c')
    s1.push('d')
    len(s0) == 2
    len(s1) == 4
    s0[0], s1[-1] == 'a', 'b'
    s1[0], s1[-1] == 'a', 'd'
    tuple(s1) == ('a', 'b', 'c', 'd')
    s1.pop() == 'd'
"""
    def __init__(self, parent=None):
        super(ExecStack, self).__init__()
        self.stack = []
        self.pos = None
        self.parent = parent
        self.lock = threading.RLock()

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.stack)

    def push(self, frame):
        """Add an item to the stack."""
        with self.lock:
            self.stack.append(frame)

    def pop(self):
        """Remove an item from the stack and return it."""
        with self.lock:
            return self.stack.pop()

    def __len__(self):
        with self.lock:
            if isinstance(self.parent, ExecStack):
                parlen = len(self.parent)
            else:
                parlen = 0
            return parlen + len(self.stack)

    def __getitem__(self, index):
        with self.lock:
            # this includes the parent stack
            return tuple(self)[index]

    def __setitem__(self, index, value):
        pass

    def __delitem__(self, index):
        pass

    def __iter__(self):
        from itertools import chain
        with self.lock:
            if self.parent is not None:
                return chain(self.parent, self.stack)
            else:
                return iter(self.stack)

    def extract(self):
        """Return lines as traceback.extract_tb, but in relation to the
execute stack, not Python's.  Includes ancestors."""
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
    """Return the current thread's execution stack."""
    return threading.currentThread().stack


class PyThread(threading.Thread):
    """Create a PyErector specific thread, with bounded semaphore and
execution stack.  Size of the bounded semaphore is from the global
Variable "pyerector.pool.size".

Calls to PyThread.run are wrapped so that exception.Error exceptions
are caught and displayed using getLogger('pyerector.execute').exception.
"""
    limiter = None

    def __init__(self, *args, **kwargs):
        if self.__class__.limiter is None:
            import logging
            logging.getLogger('pyerector.execute')\
                .debug('BoundedSemaphore(%s)', V['pyerector.pool.size'])
            self.__class__.limiter = \
                    threading.BoundedSemaphore(int(V['pyerector.pool.size'])+1)
        super(PyThread, self).__init__(*args, **kwargs)
        # this works because at _this_ time, the new thread has not been
        # created, so currentThread will still have the parent stack
        parentstack = get_current_stack()
        self.stack = ExecStack(parentstack)
        self.exception = None

    def run(self):
        import logging
        import sys
        logger = logging.getLogger('pyerector.execute')
        try:
            with self.limiter:
                logger.debug('PyThread.limiter.acquired')
                try:
                    super(PyThread, self).run()
                except Error:
                    exc = sys.exc_info()[1]
                    logger.exception('Exception in %s', self.name)
                    self.exception = exc
                    return
                except Abort:
                    return
        finally:
            logger.debug('PyThread.limiter.released')


class Initialization(object):
    """Register initialization routines and ensure that they are only
called once.  Otherwise, reimports of pyerector may result in overwriting
configuration value or augmenting subsystems (like logging) in undesirable
ways.
"""
    registry = []

    def __init__(self):
        self.been_called = False
        self.registry.append(self)

    @classmethod
    def start(cls):
        """Start calling the instances."""
        for instance in cls.registry:
            instance()

    def __call__(self):
        if self.been_called:
            return
        try:
            self.run()
        finally:
            self.been_called = True

    def run(self):
        """To be overriden."""
        pass

class InitThreading(Initialization):
    """Initialize the module, including creating an initial execution stack
on the MainThread (so get_current_stack will work in all instances).
"""
    def run(self):
        V['pyerector.pool.size'] = 10
        curthread = threading.currentThread()
        assert curthread.name == 'MainThread'
        if not hasattr(curthread, 'stack'):
            curthread.stack = ExecStack()

InitThreading()

