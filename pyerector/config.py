#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import os
import sys

__all__ = [
    'Config',
]

class Config(object):
    initialized = False
    _basedir = None
    def __init__(self, basedir=None):
        if basedir is not None:
            self.basedir = basedir
        else:
            self.basedir = os.curdir
    def _get_basedir(self):
        return self._basedir
    def _set_basedir(self, value):
        from . import debug
        dir = os.path.realpath(value)
        if dir == self._basedir:  # no change
            return
        elif os.path.isdir(dir):
            self._basedir = dir
            debug('setting Config.basedir to %s' % repr(dir))
        else:
            raise ValueError('no such file or directory: %s' % dir)
    basedir = property(_get_basedir, _set_basedir)

