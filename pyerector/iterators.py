#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import fnmatch
import glob
import itertools
import os
from .helper import normjoin
from .base import Initer, Iterator, Mapper
from .variables import V

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

class BaseIterator(Iterator):
    """Examples:
 i = Iterator('src', 'test', pattern='*.py')
 j = Iterator('build', pattern='*.py', recurse=True)
 k = Iterator('conf', ['etc/build.properties', 'tmp/dummy'], i, j)
 tuple(k) == ('conf/foo.cfg', 'etc/build.properties', 'tmp/dummy', 'src/foo.py', 'test/testfoo.py', 'build/foo.py', 'build/test/testfoo.py')

 i = Iterator('src', pattern='*.py', recurse=True)
 j = Iterator(i, pattern='test*')
 tuple(j) == ('src/test/testfoo.py',)
"""
    noglob = False
    pattern = None
    recurse = True
    fileonly = False
    exclude = ()
    def __init__(self, *path, **kwargs):
        super(BaseIterator, self).__init__(*path, **kwargs)
        self.pool = None
        self.curset = None
    def __iter__(self):
        self.pool = list(self.get_args('path'))
        self.curset = iter([])
        return super(BaseIterator, self).__iter__()
    def __next__(self):
        return self.next()
    def getnextset(self):
        basedir = V['basedir']
        def adjustglob(path, basedir=basedir):
            from glob import glob
            items = glob(os.path.join(basedir, path))
            return [n.replace(os.path.join(basedir, ''), '') for n in items]
        noglob = self.get_kwarg('noglob', bool)
        if not self.pool:
            self.logger.debug('nothing left')
            raise StopIteration
        item = self.pool[0]
        del self.pool[0]
        self.logger.debug('next item from pool is %s', repr(item))
        if isinstance(item, Iterator):
            self.curset = iter(item)
        elif isinstance(item, (tuple, list)):
            if noglob:
                self.curset = iter(item)
            else:
                items = [adjustglob(i) for i in item]
                self.logger.debug('glob seq:', items)
                self.curset = iter(reduce(lambda a,b: a+b, items))
        elif isinstance(item, str):
            if noglob:
                self.curset = iter([item])
            else:
                self.curset = iter(adjustglob(item))
        self.logger.debug('curset = %s', repr(self.curset))
    def next(self):
        noglob = self.get_kwarg('noglob', bool)
        recurse = self.get_kwarg('recurse', bool)
        pattern = self.get_kwarg('pattern', str)
        fileonly = self.get_kwarg('fileonly', bool)
        basedir = V['basedir']
        while True:
            try:
                item = next(self.curset)
            except StopIteration:
                self.logger.debug('caught StopIteration on next()')
                self.getnextset()  # can raise StopIteration
                try:
                    item = next(self.curset)  # can raise StopIteration
                except TypeError, e:
                    raise TypeError(self.curset, e)
            name = os.path.basename(item)
            # if is not excluded
            # and either:
            #    recursive and directory
            #    no pattern or matches pattern
            if (not self.exclusion.match(item) and
                ((recurse and os.path.isdir(os.path.join(basedir, item))) or
                 not pattern or fnmatch.fnmatchcase(name, pattern))):
                self.logger.debug('item = %s' % repr(item))
                break
        assert isinstance(item, str), 'Expecting a string'
        fname = os.path.join(basedir, item)
        if os.path.isdir(fname) and recurse:
            subdir = [os.path.join(item, fn) for fn in os.listdir(fname)]
            self.pool[:0] = subdir  # insert at the beginning, depth-first
            self.logger.debug('adding to pool: %s', repr(subdir))
            if fileonly:
                item = next(self)
        return item

# a helper class to handle file/directory lists better
class StaticIterator(BaseIterator):
    noglob = True

class FileIterator(BaseIterator):
    noglob = True

FileList = FileIterator

class DirList(FileIterator):
    filesonly = True

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
        self.logger.debug('mapper yields (%s, %s)', name, result)
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
                self.logger.debug('%s.uptodate() => False', self.__class__.__name__)
                return False
        else:
            self.logger.debug('%s.uptodate() => True', self.__class__.__name__)
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
            self.logger.debug('%s not found', dst)
            return False
        self.logger.debug('%s(%0.4f) %s %s(%0.4f)', src, s, (s > d and '>' or '<='), dst, d)
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
                    self.logger.debug('adding %s to fifo', normjoin(dir, fname))
                    dirs.append(normjoin(dir, fname))
                else:
                    self.logger.debug('checking %s with %s', sname, dname)
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
        self.logger.debug('%s.__call__(*%s)', klsname, args)
        srcs = FileIterator(self.get_kwarg('sources', (list, tuple, Iterator)))
        dsts = FileIterator(self.get_kwarg('destinations', (list, tuple, Iterator)))
        files = self.get_args('files')
        #self.logger.debug('srcs = %s; dsts = %s; files = %s', srcs, dsts, files)
        if not files and (not srcs or not dsts):
            self.logger.debug('%s *> %s', klsname, False)
            return False
        elif srcs and dsts:
            def get_times(lst, s=self):
                return [os.path.getmtime(s.join(f)) for f in lst]
            maxval = float('inf')
            latest_src = reduce(max, get_times(srcs), 0)
            earliest_dst = reduce(min, get_times(dsts), maxval)
            if earliest_dst == maxval: # empty list case
                self.logger.debug('%s /> %s', klsname, False)
                return False
            result = round(earliest_dst, 4) >= round(latest_src, 4)
            self.logger.debug('%s => %s', klsname, result and 'False' or 'True')
            return result
        else:
            raise RuntimeError('call uptodate()')
            return self.uptodate()

