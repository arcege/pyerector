#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.
"""Define various Iterator subclasses, for use in tasks to iterate over
files and directories.
"""

import fnmatch
import glob
import os
import re
import sys
from .helper import normjoin
from .base import Iterator, Mapper
from .variables import V

try:
    reduce
except NameError:
    try:
        from functools import reduce
    except NameError:
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


def checkglobpatt(string):
    """Check if the string has any glob characters."""
    try:
        from glob import match_check
    except ImportError:
        return re.search('[[*?]', string) is not None
    else:
        return match_check.search(string) is not None


class BaseIterator(Iterator):
    """Examples:
 i = Iterator('src', 'test', pattern='*.py')
 j = Iterator('build', pattern='*.py', recurse=True)
 k = Iterator('conf', ['etc/build.properties', 'tmp/dummy'], i, j)
 tuple(k) == ('conf/foo.cfg', 'etc/build.properties', 'tmp/dummy', 'src/foo.py', 'test/testfoo.py',
              'build/foo.py', 'build/test/testfoo.py')

 i = Iterator('src', pattern='*.py', recurse=True)
 j = Iterator(i, pattern='test*')
 tuple(j) == ('src/test/testfoo.py',)
"""
    pattern = None
    noglob = False
    recurse = False
    fileonly = True
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
        """When curset has been exhausted, find the next one in the pool.
If the next one is a glob, then evaluated it."""
        basedir = V['basedir']
        noglob = self.get_kwarg('noglob', bool)

        def adjustglob(path, noglob=noglob, basedir=basedir):
            """Return either the path in a list, or the glob of the path."""
            if noglob or not checkglobpatt(path):
                return [path]
            else:
                items = glob.glob(os.path.join(basedir, path))
                return [n.replace(os.path.join(basedir, ''), '') for n in items]
        if not self.pool:
            self.logger.debug('nothing left')
            raise StopIteration
        item = self.pool[0]
        del self.pool[0]
        self.logger.debug('next item from pool is %s', repr(item))
        if isinstance(item, Iterator):
            self.curset = iter(item)
        elif isinstance(item, (tuple, list)):
            items = [adjustglob(i) for i in item]
            if items:
                self.curset = iter(reduce(lambda a, b: a+b, items))
            else:
                self.curset = iter(())
        elif isinstance(item, str):
            self.curset = iter(adjustglob(item))
        self.logger.debug('curset = %s', repr(self.curset))

    def next(self):
        """Cycle through the curset, returning strings that would "match".
Matching strings are not in the exclusions, if a pattern is set, would
match the pattern, and if recursive and a directory.  If it is a directory,
then prepend the directory's contents to the pool (not the curset).
"""
        recurse = self.get_kwarg('recurse', bool)
        pattern = self.get_kwarg('pattern', str)
        fileonly = self.get_kwarg('fileonly', bool)
        basedir = V['basedir']
        item = None
        # search pool until we find one, raise StopIterator if we get
        # to the end; then it must match the condition at the end
        while True:
            try:
                item = next(self.curset)
            except StopIteration:
                self.logger.debug('caught StopIteration on next()')
                self.getnextset()  # can raise StopIteration
                try:
                    item = next(self.curset)  # can raise StopIteration
                except TypeError:
                    exc = sys.exc_info()[1]
                    raise TypeError(self.curset, exc)
            name = os.path.basename(item)
            # if is not excluded
            # and either:
            #    recursive and directory
            #    no pattern or matches pattern
            if self.exclusion.match(item):
                continue
            elif recurse and os.path.isdir(os.path.join(basedir, item)):
                self.logger.debug('item = %s' % repr(item))
                break
            elif not pattern or fnmatch.fnmatchcase(name, pattern):
                self.logger.debug('item = %s' % repr(item))
                break
        assert isinstance(item, str), 'Expecting a string'
        fname = os.path.join(basedir, item)
        if os.path.isdir(fname) and recurse:
            subdir = [os.path.join(item, fn) for fn in os.listdir(fname)]
            # we push this back onto the stack?
            #subdir.append( fname )
            self._prepend(subdir)  # at beginning, depth-first
            if fileonly:
                # do not use super() as it will cause a problem in FileMapper
                # similarly with just next(self)
                item = BaseIterator.next(self)
        return item

    def append(self, item):
        """Add an item to the end of the pool."""
        path = list(self.get_args('path'))
        if isinstance(item, (tuple, list)):
            path.extend(item)
        else:
            path.append(item)
        self.path = tuple(path)

    def _prepend(self, item):
        """Add a string or sequence to the beginning of the pool."""
        if isinstance(item, str):
            item = [item]
        self.pool[:0] = list(item)
        self.logger.debug('adding to pool: %s' % repr(item))


# a helper classes to handle file/directory lists better
class StaticIterator(BaseIterator):
    """By default, noglob == True."""
    noglob = True


class FileIterator(BaseIterator):
    """By default, same as BaseIterator."""

FileList = FileIterator
FileSet = FileIterator


class DirList(FileIterator):
    """By default, recurse and return both directory and file pathnames."""
    recurse = True
    fileonly = False


class FileMapper(Mapper, BaseIterator):
    """Maps source files to destination files, using a base path, destdir.
The mapper member is either a string or callable that will adjust the
basename; if None, then there is no adjustment.
The map() method can also adjust the basename.

An example of using a mapper would be:
    FileMapper(
        FileIterator('src', pattern='*.py'),
        destdir='build', mapper=lambda n: n+'c'
    )
This would map each py file in src to a pyc file in build:
    src/base.py  ->  build/base.pyc
    src/main.py  ->  build/main.pyc
"""
    destdir = None
    mapper = None

    def __init__(self, *files, **kwargs):
        super(FileMapper, self).__init__(*files, **kwargs)
        mapper = self.get_kwarg('mapper', (callable, str))
        if mapper is None:  # identity mapper
            self.mapper_func = lambda x: x
        elif callable(mapper):
            self.mapper_func = mapper
        elif isinstance(mapper, str):
            self.mapper_func = \
                lambda name, mapstr = mapper: mapstr % {'name': name}
        else:
            raise TypeError('map must be string or callable', mapper)

    def next(self):
        """Return the next item, with its mapped destination."""
        destdir = self.get_kwarg('destdir', str)
        if destdir is None:
            destdir = ''
        # do _not_ catch StopIterator
        item = super(FileMapper, self).next()
        self.logger.debug('super.next() = %s', item)
        mapped = self.mapper_func(item)
        assert isinstance(mapped, str), "mapper must return a str"
        self.logger.debug('self.map(%s) = %s', mapped, self.map(mapped))
        mapped = self.map(mapped)
        assert isinstance(mapped, str), "map() must return a str"
        result = normjoin(destdir, mapped)
        self.logger.debug('mapper yields (%s, %s)', item, result)
        return item, result

    def map(self, item):
        """Identity routine, one-to-one mapping."""
        return item

    def uptodate(self):
        """For each src,dst pair, check the modification times.  If the
dst is newer, then return True.
"""
        for (src, dst) in self:
            sfile = self.join(src)
            dfile = self.join(dst)
            if os.path.isdir(sfile):
                result = self.checktree(sfile, dfile)
            else:
                result = self.checkpair(sfile, dfile)
            if not result:
                self.logger.debug('%s.uptodate() => False',
                                  self.__class__.__name__)
                return False
        else:
            self.logger.debug('%s.uptodate() => True',
                              self.__class__.__name__)
            return True

    def checkpair(self, src, dst):
        """Return True if destination is newer than source."""
        if self.exclusion.match(os.path.basename(src)):
            return True
        try:
            srctime = round(os.path.getmtime(src), 4)
        except OSError:
            raise ValueError('no source:', src)
        try:
            dsttime = round(os.path.getmtime(dst), 4)
        except OSError:
            self.logger.debug('%s not found', dst)
            return False
        self.logger.debug('%s(%0.4f) %s %s(%0.4f)',
                          src, srctime,
                          (srctime > dsttime and '>' or '<='),
                          dst, dsttime)
        return srctime <= dsttime

    def checktree(self, src, dst):
        """Recursively check the files in both src and dst for their
modification times, using checkpair above.
"""
        dirs = [os.curdir]
        while dirs:
            cdir = dirs.pop(0)
            for fname in os.listdir(normjoin(src, cdir)):
                sname = normjoin(src, cdir, fname)
                dname = normjoin(dst, cdir, fname)
                if self.exclusion.match(fname):
                    continue
                if os.path.isdir(sname):
                    self.logger.debug('adding %s to fifo',
                                      normjoin(cdir, fname))
                    dirs.append(normjoin(cdir, fname))
                else:
                    self.logger.debug('checking %s with %s', sname, dname)
                    result = self.checkpair(sname, dname)
                    if not result:
                        return result
        else:
            return True


class BasenameMapper(FileMapper):
    """Remove the last file extension including the dot."""
    def map(self, item):
        return os.path.splitext(item)[0]


class MergeMapper(FileMapper):
    """Take only the base name, not subpaths."""
    def map(self, item):
        return os.path.basename(item)


class IdentityMapper(FileMapper):
    """Map to just the destdir value."""
    def map(self, item):
        return ''  # just use destdir

sequencetypes = (list, tuple, Iterator,
                 type(iter([])), type((None for i in ())))


class Uptodate(FileMapper):
    """For backward compatibility, should be using FileMapper or its other
subclasses."""
    # backward compatible interface
    sources = ()
    destinations = ()

    def __call__(self, *args):
        klsname = self.__class__.__name__
        self.logger.debug('%s.__call__(*%s)', klsname, args)
        srcs = FileIterator(self.get_kwarg('sources', sequencetypes))
        dsts = FileIterator(self.get_kwarg('destinations', sequencetypes))
        files = self.get_args('files')
        if not files and (not srcs or not dsts):
            self.logger.debug('%s *> %s', klsname, False)
            return False
        elif srcs and dsts:
            def get_times(lst, slf=self):
                """Return the times as a list."""
                times = []
                for fname in lst:
                    try:
                        times.append(os.path.getmtime(slf.join(fname)))
                    except OSError:
                        pass
                return times
            maxval = float('inf')
            latest_src = reduce(max, get_times(srcs), 0)
            earliest_dst = reduce(min, get_times(dsts), maxval)
            if earliest_dst == maxval:  # empty list case
                self.logger.debug('%s /> %s', klsname, False)
                return False
            result = round(earliest_dst, 4) >= round(latest_src, 4)
            self.logger.debug('%s => %s', klsname, result and 'False' or 'True')
            return result
        else:
            raise RuntimeError('call uptodate()')
            #return self.uptodate()

