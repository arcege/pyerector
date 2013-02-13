#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

__all__ = [
    'Config',
]

class Config:
    initialized = False
    _basedir = None
    def __init__(self, basedir=None):
        from os import curdir
        if basedir is not None:
            self.basedir = basedir
    def _get_basedir(self):
        return self._basedir
    def _set_basedir(self, value):
        from os.path import realpath, isdir
        dir = realpath(value)
        if isdir(dir):
            self._basedir = dir
        else:
            raise ValueError('no such file or directory: %s' % dir)
    basedir = property(_get_basedir, _set_basedir)

