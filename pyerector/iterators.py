#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import fnmatch
import glob
import itertools
import os
from .helper import normjoin
from . import debug
from .base import Initer, Iterator, Mapper

__all__ = [
    'FileSet', 'StaticIterator', 'FileIterator', 'FileList', 'DirList',
    'FileMapper', 'BasenameMapper', 'MergeMapper', 'Uptodate',
]

# a helper class to handle file/directory lists better
class StaticIterator(Iterator):
    def __init__(self, path, pattern=None, exclude=None, basedir=None):
        super(StaticIterator, self).__init__(*path,
            **{'pattern': pattern, 'exclude': exclude, 'basedir': basedir}
        )
        pool = self.get_args('path')
        if isinstance(pool, (tuple, list)):
            self.pool = list(pool)
        else:
            self.pool = [pool]
        self.poolpos = 0
        self.setpos = 0
        if self.pattern:
            # should may defer to next() method
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
        # do not use the join() method since it will remove the trailing
        # separator
        # XXX should we be returning an iter() object?
        if isinstance(pattern, Iterator): # an iterator, so convert to a list
            return list(pattern)
        base = os.path.join(self.config.basedir, '')
        files = glob.glob(self.join(pattern))
        debug('%s.glob(%s) = %s' % (self.__class__.__name__, self.join(pattern), files))
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
                for name in os.listdir(os.path.join(self.config.basedir, thisdir)):
                    spath = os.path.join(thisdir, name)
                    dpath = os.path.join(self.config.basedir, thisdir, name)
                    if self.apply_exclusion(name):
                        pass
                    elif os.path.islink(dpath) or os.path.isfile(dpath):
                        paths.append(spath)
                    elif self.recurse:
                        dirs.append(spath)
        self.pool[:] = paths # replace the pool with the gathered set

class FileSet(Iterator):
    klass = StaticIterator
    def __init__(self, *set, **kwargs):
        from .base import Initer
        super(FileSet, self).__init__(*set, **kwargs)
        self.set = []
        for item in set:
            if not isinstance(item, self.klass):
                item = self.klass(item)
            self.set.append(item)
    def append(self, item):
        if not isinstance(item, self.klass):
            item = self.klass(item)
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

class FileMapper(Mapper):
    files = ()
    destdir = None
    map = None
    mapper = None
    def __init__(self, *files, **kwargs):
        if len(files) == 1 and isinstance(files[0], (FileIterator, FileSet)):
            files = files[0]
        elif len(files) == 1 and isinstance(files[0], (tuple, list)):
            files = FileIterator(files[0])
        elif len(files) == 1:
            files = FileIterator((files[0],))
        else:
            files = FileIterator(files)
        super(FileMapper, self).__init__(*files, **kwargs)
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
        self.queue = []
        self.ifiles = None
    def __iter__(self):
        self.ifiles = iter(self.get_args('files'))
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
            except (StopIteration, IndexError):
                self.ifiles = None
                raise StopIteration
            except TypeError:
                raise RuntimeError('not called as an iter object')
            self.pos += 1
            mapped = self.map(self.mapper(name))
            assert callable(self.mapper), 'mapper is not callable'
            mapped = self.mapper(name)
            if isinstance(mapped, (list, tuple)):
                first = mapped[0]
                self.queue.extend( [(name, m) for m in mapped[1:]] )
                mapped = first
        destdir = self.get_kwarg('destdir', str)
        if destdir is None:
            destdir = ''
        result = normjoin(destdir, self.map(mapped))
        debug('mapper yields (%s, %s)' % (name, result))
        return (name, result)
    def map(self, fname):
        return fname
    def uptodate(self):
        for (s, d) in self:
            sf = self.join(s)
            df = self.join(d)
            if os.path.isdir(sf):
                result = self.checktree(sf, df)
            else:
                result = self.checkpair(sf, df)
            if not result:
                debug('%s.uptodate() => False' % self.__class__.__name__)
                return False
        else:
            debug('%s.uptodate() => True' % self.__class__.__name__)
            return True
    @staticmethod
    def checkpair(src, dst):
        """Return True if destination is newer than source."""
        try:
            s = round(os.path.getmtime(src), 4)
        except OSError:
            raise ValueError('no source:', src)
        try:
            d = round(os.path.getmtime(dst), 4)
        except OSError:
            return False
        return d >= s
    @classmethod
    def checktree(cls, src, dst):
        return False # always outofdate until we implement

class BasenameMapper(FileMapper):
    """Remove the last file extension including the dot."""
    def map(self, fname):
        return os.path.splitext(fname)[0]

class MergeMapper(FileMapper):
    def map(self, fname):
        return self.join(self.destdir)

class Uptodate(FileMapper):
    # backward compatible interface
    sources = ()
    destinations = ()
    def __call__(self, *args):
        debug('%s.__call__(*%s)' % (self.__class__.__name__, args))
        klsname = self.__class__.__name__
        srcs = self.get_kwarg('sources', (list, tuple, Iterator))
        dsts = self.get_kwarg('destinations', (list, tuple, Iterator))
        if not self.files and (not srcs or not dsts):
            debug(klsname, '*>', False)
            return False
        if srcs and dsts:
            def get_times(lst, s=self):
                return [os.path.getmtime(s.join(f)) for f in lst]
            maxval = float('inf')
            lastest_src = reduce(max, get_times(self.get_files(srcs)), 0)
            earliest_dst = reduce(max, get_times(self.get_files(dsts)), maxval)
            if earliest_dst == maxval: # empty list case
                return False
            result = round(earliest_dst, 4) >= round(latest_src, 4)
            debug(klsname, '=>', result and 'False' or 'True')
            return result
        else:
            return self.uptodate()

