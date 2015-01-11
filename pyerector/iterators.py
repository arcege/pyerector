#!/usr/bin/python
# Copyright @ 2012-2015 Michael P. Reilly. All rights reserved.
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
    'FileMapper', 'BasenameMapper', 'MergeMapper', 'IdentityMapper',
    'Uptodate',
]



class FileIterator(Iterator):
    """File-based subclass of Iterator.
Default parameters: pattern=None, noglob=False, recurse=False,
fileonly=True, exclude=()."""
    def adjust(self, candidate):
        basedir = V['basedir']
        noglob = self.get_kwarg('noglob', bool)
        if isinstance(candidate, Iterator):
            return list(candidate)
        elif not isinstance(candidate, str):
            raise TypeError('%s is not a string' % repr(candidate))
        if noglob or not self.checkglobpatt(candidate):
            return super(FileIterator, self).adjust(candidate)
        else:
            items = glob.glob(os.path.join(basedir, candidate))
            return [n.replace(os.path.join(basedir, ''), '') for n in items]

    def post_process_candidate(self, candidate):
        basedir = V['basedir']
        recurse = self.get_kwarg('recurse', bool)
        fileonly = self.get_kwarg('fileonly', bool)
        if recurse and os.path.isdir(os.path.join(basedir, candidate)):
            fnames = [os.path.join(candidate, fn) for fn in
                os.listdir(os.path.join(basedir, candidate))
            ]
            self._prepend(fnames)
            if fileonly:
                candidate = FileIterator.next(self)
        return candidate


    def check_candidate(self, candidate):
        basedir = V['basedir']
        recurse = self.get_kwarg('recurse', bool)
        pattern = self.get_kwarg('pattern', str)
        if recurse and os.path.isdir(os.path.join(basedir, candidate)):
            return True
        elif not pattern or \
                fnmatch.fnmatchcase(os.path.basename(candidate), pattern):
            return True
        else:
            return False

    @staticmethod
    def checkglobpatt(string):
        """Check if the string has any glob characters."""
        try:
            from glob import match_check
        except ImportError:
            return re.search('[[*?]', string) is not None
        else:
            return match_check.search(string) is not None


# a helper classes to handle file/directory lists better
class StaticIterator(Iterator):
    """By default, noglob == True."""
    noglob = True

FileList = FileIterator
FileSet = FileIterator


class DirList(FileIterator):
    """By default, recurse and return both directory and file pathnames.
Default params: recurse=True, fileonly=False."""
    recurse = True
    fileonly = False


class FileMapper(Mapper, FileIterator):
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
    [('src/base.py', 'build/base.pyc'), ('src/main.py', 'build/main.pyc')]
"""

    def checkpair(self, src, dst):
        sfile = self.join(src)
        dfile = self.join(dst)
        """Return True if destination is newer than source."""
        if self.exclusion.match(os.path.basename(sfile)):
            return True
        try:
            srctime = round(os.path.getmtime(sfile), 4)
        except OSError:
            raise ValueError('no source:', src)
        try:
            dsttime = round(os.path.getmtime(dfile), 4)
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
        sources = self.get_kwarg('sources', sequencetypes)
        if isinstance(sources, Iterator):
            srcs = sources
        else:
            srcs = FileIterator(sources)
        destinations = self.get_kwarg('destinations', sequencetypes)
        if isinstance(destinations, Iterator):
            dsts = destinations
        else:
            dsts = FileIterator(destinations)
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

