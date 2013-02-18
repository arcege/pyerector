#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import fnmatch
import glob
import os
from .helper import normjoin
from . import debug

__all__ = [
    'FileIterator', 'FileList', 'DirList'
]

# a helper class to handle file/directory lists better
class FileIterator(object):
    def __init__(self, path, pattern=None, exclude=None, basedir=None):
        # load it here to avoid recursive imports
        from .base import Initer
        self.basedir = basedir or Initer.config.basedir
        super(FileIterator, self).__init__()
        if isinstance(path, (tuple, list)):
            self.pool = list(path)
        else:
            self.pool = [path]
        self.poolpos = 0
        self.setpos = 0
        self.exclude = exclude
        self.pattern = pattern
        if self.pattern:
            for i, v in enumerate(self.pool):
                self.pool[i] = os.path.join(v, self.pattern)
        self.curpoolitem = None
        self.curpoolset = None
    def __iter__(self):
        self.poolpos = 0
        self.setpos = 0
        self.curpoolitem = None
        self.curpoolset = None
        return self
    def next(self):
        if self.curpoolitem is None:
            self.getnextset()
        while True:
            if self.setpos >= len(self.curpoolset):
                self.getnextset()
            item = self.curpoolset[self.setpos]
            self.setpos += 1
            if not self.apply_exclusion(item):
                return item
    def getnextset(self):
        while True:
            if self.poolpos >= len(self.pool):
                raise StopIteration
            self.curpoolitem = self.pool[self.poolpos]
            self.poolpos += 1
            self.curpoolset = self.glob(self.curpoolitem)
            self.setpos = 0
            if self.curpoolset:
                break
    def glob(self, pattern):
        base = os.path.join(self.basedir, '')
        files = glob.glob(os.path.join(self.basedir, pattern))
        return [name.replace(base, '') for name in files]
    def apply_exclusion(self, filename):
        result = self.exclude and fnmatch.fnmatch(filename, self.exclude)
        #debug('apply_exclusion(%s, %s) =' % (filename, self.exclude),
        #        result)
        return result
class FileList(FileIterator):
    def __init__(self, *args, **kwargs):
        super(FileList, self).__init__(path=args, **kwargs)

class DirList(FileIterator):
    def __init__(self, path, recurse=False, filesonly=True, **kwargs):
        super(DirList, self).__init__(path, **kwargs)
        self.recurse = bool(recurse)
        self.filesonly = bool(filesonly)
        self.update_dirpath()
    def update_dirpath(self):
        dirs = self.pool[:]
        paths = []
        while dirs:
            thisdir = dirs[0]
            del dirs[0]
            if not self.filesonly:
                paths.append(thisdir)
            if not self.apply_exclusion(os.path.basename(thisdir)):
                for name in os.listdir(os.path.join(self.basedir, thisdir)):
                    spath = os.path.join(thisdir, name)
                    dpath = os.path.join(self.basedir, thisdir, name)
                    if self.apply_exclusion(name):
                        pass
                    elif os.path.islink(dpath) or os.path.isfile(dpath):
                        paths.append(spath)
                    elif self.recurse:
                        dirs.append(spath)
        self.pool[:] = paths # replace the pool with the gathered set

