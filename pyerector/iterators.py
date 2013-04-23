#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import fnmatch
import glob
import itertools
import os
from .helper import normjoin
from . import debug
from .base import Initer, Iterator, Mapper

try:
    reduce
except NameError:
    try:
        from functools import reduce
    except:
        # we shouldn't get here, but...
        def reduce(function, iterable, initializer=None):
            """Iterate over a sequence, calling function on each successive
item, accumulating the result."""
            accum = initializer
            for item in iterable:
                if accum is None:
                    accum = item
                else:
                    accum = function(accum, item)
            else:
                if accum is None and initializer is not None:
                    return initializer
            return accum

__all__ = [
    'FileSet', 'StaticIterator', 'FileIterator', 'FileList', 'DirList',
    'FileMapper', 'BasenameMapper', 'MergeMapper', 'Uptodate',
]

# a helper class to handle file/directory lists better
class StaticIterator(Iterator):
    pattern = None
    exclude = ()
    def __init__(self, path, **kwargs):
        super(StaticIterator, self).__init__(*path, **kwargs)
        pool = self.get_args('path')
        if isinstance(pool, (tuple, list)):
            self.pool = list(pool)
        else:
            self.pool = [pool]
        self.poolpos = 0
        self.setpos = 0
        pattern = self.get_kwarg('pattern', str)
        if pattern:
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
        return super(StaticIterator, self).__iter__()
    def __next__(self):
        return self.next()
    def next(self):
        if self.curpoolitem is None:
            self.getnextset()
        while True:
            if self.setpos >= len(self.curpoolset):
                self.getnextset()
            item = self.curpoolset[self.setpos]
            self.setpos += 1
            if not self.exclusion.match(item):
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
            if not self.exclusion.match(os.path.basename(thisdir)):
                for name in os.listdir(os.path.join(self.config.basedir, thisdir)):
                    spath = os.path.join(thisdir, name)
                    dpath = os.path.join(self.config.basedir, thisdir, name)
                    if self.exclusion.match(name):
                        pass
                    elif os.path.islink(dpath) or os.path.isfile(dpath):
                        paths.append(spath)
                    elif self.recurse:
                        dirs.append(spath)
        self.pool[:] = paths # replace the pool with the gathered set

class FileSet(Iterator):
    klass = StaticIterator
    exclude = None
    def __init__(self, *set, **kwargs):
        super(FileSet, self).__init__(*set, **kwargs)
        self.set = []
        for item in set:
            self.append(item)
    def append(self, item):
        klass = self.get_kwarg('klass', type(Iterator))
        if isinstance(item, (tuple, list)):
            item = klass(item)
        elif not isinstance(item, Iterator):
            item = klass((item,))
        self.set.append(item)
    def __iter__(self):
        self.iset = iter(self.set)
        self.cur = None
        return super(FileSet, self).__iter__()
    def __next__(self):
        return self.next()
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
    exclude = None
    iteratorclass = FileIterator
    def __init__(self, *files, **kwargs):
        if 'iteratorclass' in kwargs:
            self.iteratorclass = kwargs['iteratorclass']
        if len(files) == 1 and isinstance(files[0], Iterator):
            files = files[0]
        elif len(files) == 1 and isinstance(files[0], (tuple, list)):
            files = self.iteratorclass(files[0])
        elif len(files) == 1:
            files = self.iteratorclass((files[0],))
        else:
            files = FileSet(files, klass=self.iteratorclass)
        # we should end up with 'files' being a single Iterator instance
        super(FileMapper, self).__init__(*files, **kwargs)
        mapper = self.get_kwarg('mapper', (callable, str))
        if mapper is None:  # identity mapper
            self.mapper_func = lambda x: x
        elif callable(mapper):
            self.mapper_func = mapper
        elif isinstance(mapper, str):
            self.mapper_func = \
                lambda name, mapstr=mapper: mapstr % {'name': name}
        else:
            raise TypeError('map must be string or callable', mapper)
        self.pos = 0
        self.queue = []
        self.ifiles = None
    def __iter__(self):
        self.ifiles = iter(self.get_args('files'))
        self.pos = 0
        self.queue = []
        return super(FileMapper, self).__iter__()
    def __next__(self):
        return self.next()
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
            assert callable(self.mapper_func), 'mapper is not callable'
            mapped = self.mapper_func(name)
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
    def checkpair(self, src, dst):
        """Return True if destination is newer than source."""
        if self.exclusion.match(os.path.basename(src)):
            return True
        try:
            s = round(os.path.getmtime(src), 4)
        except OSError:
            raise ValueError('no source:', src)
        try:
            d = round(os.path.getmtime(dst), 4)
        except OSError:
            debug('%s not found' % dst)
            return False
        debug('%s(%0.4f) %s %s(%0.4f)' % (src, s, (s > d and '>' or '<='), dst, d))
        return s <= d
    def checktree(self, src, dst):
        dirs = [os.curdir]
        while dirs:
            dir = dirs.pop(0)
            ndir = normjoin(src, dir)
            for fname in os.listdir(normjoin(src, dir)):
                sname = normjoin(src, dir, fname)
                dname = normjoin(dst, dir, fname)
                if self.exclusion.match(fname):
                    continue
                if os.path.isdir(sname):
                    debug('adding %s to fifo' % normjoin(dir, fname))
                    dirs.append(normjoin(dir, fname))
                else:
                    debug('checking %s with %s' % (sname, dname))
                    result = self.checkpair(sname, dname)
                    if not result:
                        return result
        else:
            return True

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
        klsname = self.__class__.__name__
        debug('%s.__call__(*%s)' % (klsname, args))
        srcs = self.get_kwarg('sources', (list, tuple, Iterator))
        dsts = self.get_kwarg('destinations', (list, tuple, Iterator))
        files = self.get_args('files')
        #debug('srcs =', srcs, 'dsts =', dsts, 'files =', files)
        if not files and (not srcs or not dsts):
            debug(klsname, '*>', False)
            return False
        elif srcs and dsts:
            def get_times(lst, s=self):
                return [os.path.getmtime(s.join(f)) for f in lst]
            maxval = float('inf')
            latest_src = reduce(max, get_times(self.get_files(srcs)), 0)
            earliest_dst = reduce(min, get_times(self.get_files(dsts)), maxval)
            if earliest_dst == maxval: # empty list case
                return False
            result = round(earliest_dst, 4) >= round(latest_src, 4)
            debug(klsname, '=>', result and 'False' or 'True')
            return result
        else:
            raise RuntimeError('call uptodate()')
            return self.uptodate()

