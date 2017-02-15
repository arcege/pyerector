#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.
"""Define various Iterator subclasses, for use in tasks to iterate over
files and directories.
"""

try:
    reduce
except NameError:
    try:
        # pylint: disable=redefined-builtin
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
            if accum is None and initializer is not None:
                return initializer
            return accum

import re
from .path import Path
from .base import Iterator, Mapper
from .variables import V

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
        if isinstance(basedir, str):
            basedir = Path(basedir)
        noglob = self.get_kwarg('noglob', bool)
        if isinstance(candidate, Iterator):
            return list(candidate)
        elif not isinstance(candidate, (Path, str)):
            raise TypeError('%s is not a string' % repr(candidate))
        elif isinstance(candidate, str):
            candidate = Path(candidate)
        if noglob or not self.checkglobpatt(candidate):
            return super(FileIterator, self).adjust(candidate)
        else:
            glist = basedir.glob(candidate.value)
            self.logger.debug('glob(%s) = %s', candidate, glist)
            return [(c - basedir) for c in glist]

    def post_process_candidate(self, candidate):
        basedir = V['basedir']
        if not isinstance(basedir, Path):
            basedir = Path(basedir)
        recurse = self.get_kwarg('recurse', bool)
        fileonly = self.get_kwarg('fileonly', bool)
        if isinstance(candidate, tuple):  # for a Mapper
            # pylint: disable=redefined-variable-type
            cand = (basedir + candidate[0], basedir + candidate[1])
        else:
            # pylint: disable=redefined-variable-type
            cand = basedir + candidate
        #print 'candidate', repr(c)
        if recurse and cand.isdir:
            self._prepend([(i - basedir) for i in cand])
            if fileonly:
                candidate = FileIterator.next(self)
        return candidate


    def check_candidate(self, candidate):
        candidate = candidate
        basedir = V['basedir']
        recurse = self.get_kwarg('recurse', bool)
        pattern = self.get_kwarg('pattern', str)
        cand = basedir + candidate
        if recurse and cand.isdir:
            return True
        elif not pattern or cand.match(pattern):
            return True
        else:
            return False

    @staticmethod
    def checkglobpatt(string):
        """Check if the string has any glob characters."""
        try:
            from glob import match_check
        except ImportError:
            return re.search('[[*?]', str(string)) is not None
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
        """Return True if destination is newer than source."""
        sfile = self.join(src)
        dfile = self.join(dst)
        if self.exclusion.match(sfile):
            return True
        try:
            if sfile.exists:
                srctime = round(sfile.mtime, 4)
            else:
                raise ValueError('no source:', src)
        except OSError:
            raise ValueError('no source:', src)
        try:
            if dfile.exists:
                dsttime = round(dfile.mtime, 4)
            else:
                self.logger.debug('%s not found', dst)
                return False
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
        dirs = [src]
        while dirs:
            cdir = dirs.pop(0)
            for sname in cdir:
                dname = dst + (sname - src)
                if self.exclusion.match(sname):
                    continue
                if sname.isdir:
                    self.logger.debug('adding %s to fifo', sname)
                    dirs.append(sname)
                else:
                    self.logger.debug('checking %s with %s', sname, dname)
                    result = self.checkpair(sname, dname)
                    if not result:
                        return result
        return True


class BasenameMapper(FileMapper):
    """Remove the last file extension including the dot."""
    def map(self, item):
        return item.delext()


class MergeMapper(FileMapper):
    """Take only the base name, not subpaths."""
    def map(self, item):
        return item.basename


class IdentityMapper(FileMapper):
    """Map to just the destdir value."""
    def map(self, item):
        return Path('.')  # just use destdir

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
            maxval = float('inf')
            latest_src = reduce(max, [f.mtime for f in srcs if f.exists], 0)
            earliest_dst = reduce(min, [f.mtime for f in dsts if f.exists],
                                  maxval)
            if earliest_dst == maxval:  # empty list case
                self.logger.debug('%s /> %s', klsname, False)
                return False
            result = round(earliest_dst, 4) >= round(latest_src, 4)
            self.logger.debug('%s => %s', klsname, result and 'False' or 'True')
            return result
        else:
            raise RuntimeError('call uptodate()')
