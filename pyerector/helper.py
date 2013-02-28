#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import os
from sys import version

__all__ = [
    'normjoin',
]

class Verbose(object):
    from os import linesep as eoln
    from sys import stdout as stream
    prefix = ''
    def __init__(self, state=False):
        from os import environ
        self.state = bool(state)
        if 'PYERECTOR_PREFIX' in environ:
            self.prefix = environ['PYERECTOR_PREFIX'].decode('UTF-8')
    def __bool__(self):
        return self.state
    __nonzero__ = __bool__
    def on(self):
        self.state = True
    def off(self):
        self.state = False
    def write(self, msg):
        if self.prefix != '':
            self.stream.write(u(self.prefix))
            self.stream.write(u(': '))
        self.stream.write(u(msg))
        self.stream.write(u(self.eoln))
        self.stream.flush()
    def __call__(self, *args):
        if self.state:
            self.write(u(' ').join([u(str(s)) for s in args]))

# helper routines
def normjoin(*args):
    return os.path.normpath(os.path.join(*args))

if version < '3':
    def u(x):
        from codecs import unicode_escape_decode
        return unicode_escape_decode(x)[0]
else:
    def u(x):
        return x

