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

import os
import re
import sys

from .path import Path
from .variables import V
from .helper import Exclusions
from .base import Initer

__all__ = [
    'FileSet', 'StaticIterator', 'FileIterator', 'FileList', 'DirList',
    'FileMapper', 'BasenameMapper', 'MergeMapper', 'IdentityMapper',
    'Uptodate',
]


class Iterator(Initer):
    """The base class for Iterators and Mappers.  Processes arguments as
sequences of files.
Examples:
 i = Iterator('src', 'test', pattern='*.py')
 j = Iterator('build', pattern='*.py', recurse=True)
 k = Iterator('conf', ['etc/build.properties', 'tmp/dummy'], i, j)
 tuple(k) == ('conf/foo.cfg', 'etc/build.properties', 'tmp/dummy',
              'src/foo.py', 'test/testfoo.py', 'build/foo.py',
              'build/test/testfoo.py')

 i = Iterator('src', pattern='*.py', recurse=True)
 j = Iterator(i, pattern='test*')
 tuple(j) == ('src/test/testfoo.py',)
"""
    exclusion = Exclusions()

    def __init__(self, *path, **kwargs):
        super(Iterator, self).__init__(*path, **kwargs)
        self.pool = None
        self.curset = None
        exclude = self.get_kwarg(
            'exclude', (Exclusions, set, str, tuple, list, type(None))
        )
        if isinstance(exclude, Exclusions):
            self.exclusion = exclude
        elif isinstance(exclude, (set, tuple, list)):
            self.exclusion = Exclusions(exclude)
        elif isinstance(exclude, str):
            self.exclusion = Exclusions((exclude,))
        self.path = None

    def __repr__(self):
        if hasattr(self, 'args') and isinstance(self.args, tuple):
            return '<%s %s>' % (self.__class__.__name__, self.args)
        else:
            return '<%s ()>' % (self.__class__.__name__,)

    def __call__(self):
        """Iterators and Mappers do not get called as Targets, Tasks and
Sequentials."""
        raise NotImplementedError

    def __iter__(self):
        # this is a list so we can modify it later, if necessary
        self.pool = list(self.get_args('path'))
        self.curset = iter([])
        return self

    def __next__(self):
        return self.next()

    def next(self):
        """Cycle through the curset, returning strings that would "match".
Matching strings are not in the exclusions, if a pattern is set, would
match the pattern, and if recursive and a directory.  If it is a directory,
then prepend the directory's contents to the pool (not the curset).
"""
        while True:
            try:
                candidate = next(self.curset)
            except StopIteration:
                #self.logger.debug('caught StopIteration on next()')
                self.getnextset()  # can raise StopIteration
                try:
                    candidate = next(self.curset)  # can raise StopIteration
                except TypeError:
                    exc = sys.exc_info()[1]
                    raise TypeError(self.curset, exc)
            if isinstance(candidate, tuple) and len(candidate) == 2:
                break
            if not isinstance(candidate, Path):
                candidate = Path(candidate)
            if self.exclusion.match(candidate):
                continue
            self.logger.debug('candidate = %s', repr(candidate))
            if self.check_candidate(candidate):
                break
        assert isinstance(candidate, (Path, str, tuple)), candidate
        return self.post_process_candidate(candidate)

    def getnextset(self):
        """Set state to the next item in the set."""
        if not self.pool:
            self.logger.debug('nothing left')
            raise StopIteration
        item = self.pool.pop(0)
        self.logger.debug('next item from pool is %s', repr(item))
        if isinstance(item, Iterator):
            items = item
        elif isinstance(item, MapperPair):
            items = [item]
        elif isinstance(item, (tuple, list)):
            items = [
                i for subitems in [self.adjust(i) for i in item]
                for i in subitems
            ]
        elif isinstance(item, (Path, str)):
            items = self.adjust(item)
        self.curset = iter(items)
        #self.logger.debug('curset = %s', repr(self.curset))

    def append(self, item):
        """Add an item to the end of the pool."""
        path = list(self.get_args('path'))
        if isinstance(item, Iterator):
            path.extend(item)
        elif isinstance(item, (tuple, list)):
            path.extend([Path(i) for i in item])
        elif isinstance(item, (MapperPair, Path)):
            path.append(item)
        else:
            path.append(Path(item))
        self.path = tuple(path)

    def _prepend(self, item):
        """Add a string or sequence to the beginning of the pool."""
        if isinstance(item, str):
            item = [Path(item)]
        elif isinstance(item, (MapperPair, Path)):
            item = [item]
        else:
            item = [Path(i) for i in item]
        self.pool[:0] = item
        self.logger.debug('adding to pool: %s', repr(item))

    # text based
    # pylint: disable=no-self-use
    def post_process_candidate(self, candidate):
        """Return the candidate. To be overridden."""
        return candidate

    # pylint: disable=no-self-use
    def adjust(self, candidate):
        """Return a list of the candidate as a Path object.
To be overridden."""
        return [Path(candidate)]

    def check_candidate(self, candidate):
        """Return true if the candidate matches the pattern or
if there is no pattern.  To be overridden."""
        pattern = self.get_kwarg('pattern', str)
        if not pattern:
            return True
        else:
            return candidate.match(pattern)


class MapperPair(tuple):
    def __new__(self, src, dst):
        return super(MapperPair, self).__new__(self, (src, dst))
    @property
    def src(self):
        return self[0]
    @property
    def dst(self):
        return self[1]

class Mapper(Iterator):
    """Maps source files to destination files, using a base path, destdir.
The mapper member is either a string or callable that will adjust the
basename; if None, then there is no adjustment.
The map() method can also adjust the basename.

An example of using a mapper would be:
    FileMapper(
        FileIterator('src', pattern='*.py'),
        destdir='build', mapper=lambda n: n+'c'
        destdir='build', mapper='%(name)sc'
    )
This would map each py file in src to a pyc file in build:
    src/base.py  ->  build/base.pyc
    src/main.py  ->  build/main.pyc
"""
    destdir = None
    mapper = None
    def __init__(self, *files, **kwargs):
        super(Mapper, self).__init__(*files, **kwargs)
        mapper = self.get_kwarg('mapper', (callable, str))
        if mapper is None:  # identity mapper
            self.mapper_func = Path
        elif callable(mapper):
            self.mapper_func = mapper
        elif isinstance(mapper, str):
            # pylint: disable=redefined-variable-type
            self.mapper_func = \
                lambda name, mapstr=mapper: Path(mapstr % {'name': name})
        else:
            raise TypeError('map must be string or callable', mapper)

    def next(self):
        """Return the next item, with its mapped destination."""
        destdir = self.get_kwarg('destdir', (Path, str))
        if destdir is None:
            destdir = Path(os.curdir)
        # do _not_ catch StopIteration
        item = super(Mapper, self).next()
        #self.logger.debug('super.next() = %s', item)
        if isinstance(item, tuple) and len(item) == 2:
            item, temp = item
            mapped = self.mapper_func(temp)
            del temp
        else:
            mapped = self.mapper_func(item)
        assert isinstance(mapped, (Path, str)), "mapper must return a str"
        result = self.map(mapped)
        self.logger.debug(
            'self.map(%s) = %s[%s]', mapped, repr(result), type(result)
        )
        mapped = result
        assert isinstance(mapped, (Path, str)), \
            'map() must return a str or Path'
        result = destdir + mapped #normjoin(destdir, mapped)
        self.logger.debug('mapper yields (%s, %s)', item, result)
        return MapperPair(item, result)

    # pylint: disable=no-self-use
    def map(self, item):
        """Identity routine, one-to-one mapping."""
        if isinstance(item, Path):
            return item
        else:
            return Path(item)

    def __call__(self, *args):
        for (src, dst) in self:
            if not self.checkpair(src, dst):
                break
        else:
            self.logger.debug('%s() => True', self)
            return True
        self.logger.debug('%s() => False', self)
        return False

    def uptodate(self):
        """For each src,dst pair, check the modification times.  If the
dst is newer, then return True.
"""
        return self()  # run __call__

    def checkpair(self, src, dst):
        """To be overridden."""
        self.logger.debug('%s.checkpair(%s, %s)', self, src, dst)
        return False

    # pylint: disable=no-self-use,unused-argument
    def checktree(self, src, dst):
        """To be overridden."""
        return False



# pylint: disable=abstract-method
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
# pylint: disable=abstract-method
class StaticIterator(Iterator):
    """By default, noglob == True."""
    noglob = True

FileList = FileIterator
FileSet = FileIterator


# pylint: disable=abstract-method
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
        from .helper import newer
        sfile = self.join(src)
        dfile = self.join(dst)
        if self.exclusion.match(sfile):
            return True
        if not sfile.exists:
            raise OSError('no source:', src)
        return newer(sfile, dfile, logger=self.logger)

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

SequenceTypes = (list, tuple, Iterator,
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
        sources = self.get_kwarg('sources', SequenceTypes)
        if isinstance(sources, Iterator):
            srcs = sources
        else:
            srcs = FileIterator(sources)
        destinations = self.get_kwarg('destinations', SequenceTypes)
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
