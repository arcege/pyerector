#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import fnmatch
import glob
import itertools
import os
from .helper import normjoin
from . import debug

__all__ = [
    'FileSet', 'StaticIterator', 'FileIterator', 'FileList', 'DirList',
    'FileMapper', 'BasenameMapper',
]

# a helper class to handle file/directory lists better
class StaticIterator(object):
    def __init__(self, path, pattern=None, exclude=None, basedir=None):
        # load it here to avoid recursive imports
        from .base import Initer
        self.basedir = basedir or Initer.config.basedir
        super(StaticIterator, self).__init__()
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
        return [pattern]
    def apply_exclusion(self, filename):
        result = self.exclude and fnmatch.fnmatch(filename, self.exclude)
        #debug('apply_exclusion(%s, %s) =' % (filename, self.exclude),
        #        result)
        return result

class FileIterator(StaticIterator):
    def glob(self, pattern):
        base = os.path.join(self.basedir, '')
        files = glob.glob(os.path.join(self.basedir, pattern))
        return [name.replace(base, '') for name in files]

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

class FileSet(object):
    klass = StaticIterator
    def __init__(self, *set, **kwargs):
        from .base import Initer
        super(FileSet, self).__init__()
        self.basedir = kwargs.get('basedir', Initer.config.basedir)
        self.set = []
        for item in set:
            if not isinstance(item, self.klass):
                item = self.klass(item, basedir=self.basedir)
            self.set.append(item)
    def append(self, item):
        if not isinstance(item, self.klass):
            item = self.klass(item, basedir=self.basedir)
        self.set.append(item)
    def __iter__(self):
        self.iset = iter(self.set)
        self.cur = None
        return self
    def next(self):
        while True:
            if self.cur is None:
                n = next(self.iset)  # pass StopIteration through
                self.cur = iter(n)
            try:
                item = next(self.cur)
            except StopIteration:
                self.cur = None
            else:
                return item

class FileMapper(object):
    def __init__(self, *files, **kwargs):
        from .base import Initer
        super(FileMapper, self).__init__()
        self.basedir = kwargs.get('basedir', Initer.config.basedir)
        #print files
        #print files[0], type(files[0]), isinstance(files[0], FileSet)
        if len(files) == 1 and isinstance(files[0], (FileIterator, FileSet)):
            #print 'single iterator/set'
            self.files = files[0]
        elif len(files) == 1 and isinstance(files[0], (tuple, list)):
            #print 'single sequence'
            self.files = FilesIterator(files[0], basedir=self.basedir)
        elif isinstance(files, (FileIterator, FileSet)):
            #print 'tuple was iterator/set - bad'
            self.files = files
        else:
            #print 'convert to iterator'
            self.files = FileIterator(files, basedir=self.basedir)
        self.destdir = 'destdir' in kwargs and kwargs['destdir'] or os.curdir
        if 'map' in kwargs:
            mapper = kwargs['map']
            if callable(mapper):
                self.mapper = mapper
            elif isinstance(mapper, str):
                self.mapper = \
                    lambda name, mapstr=mapper: mapstr % {'name': name}
            else:
                raise TypeError('map must be string or callable', mapper)
        else:  # identity mapper
            self.mapper = lambda x: x
        self.pos = 0
    def __iter__(self):
        self.ifiles = iter(self.files)
        self.pos = 0
        self.queue = []
        return self
    def next(self):
        if self.queue:
            name, mapped = self.queue[0]
            del self.queue[0]
        else:
            try:
                name = next(self.ifiles)
            except IndexError:
                raise StopIteration
            self.pos += 1
            mapped = self.map(self.mapper(name))
            assert callable(self.mapper), 'mapper is not callable'
            mapped = self.mapper(name)
            if isinstance(mapped, (list, tuple)):
                first = mapped[0]
                self.queue.extend( [(name, m) for m in mapped[1:]] )
                mapped = first
        result = normjoin(self.destdir, self.map(mapped))
        debug('mapper yields (%s, %s)' % (name, result))
        return (name, result)
    def map(self, fname):
        return fname

class BasenameMapper(FileMapper):
    """Remove the last file extension including the dot."""
    def map(self, fname):
        return os.path.splitext(fname)[0]


