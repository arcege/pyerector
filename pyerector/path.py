#!/usr/bin/python
# Copyright @ 2012-2015 Michael P. Reilly. All rights reserved.
"""A unified file system object class - the purpose of this is
to avoid having to stringify values being passed to explicit calls
to os.* and os.path.* functions."""

from logging import getLogger
import os

__all__ = [
    'Path',
    'homedir',
    'rootdir',
]


class Path(object):
    """Represent a file system pathname, with standard posix properties
and operations."""

    class TYPE:
        DIR = 'dir'
        FILE = 'file'
        LINK = 'link'
        NOENT = 'noentry'
        OTHER = 'other'
        PIPE = 'pipe'

    sep = os.sep

    def __init__(self, *components):
        from .variables import Variable
        comps = []
        self.has_variable = False
        for c in components:
            if isinstance(c, Path):
                if c.isabs:
                    comps[:] = c.components[:]
                    continue
                else:
                    s = c.components[:]
            elif isinstance(c, Variable):
                s = (c,)
                self.has_variable = True
            else:
                s = self._normalize(self._split(c))
            # handle later as absolute
            if s and s[0] == '':
                comps = s[:]
            else:
                comps.extend(s)
        if len(comps) == 0:
            self.components = [os.curdir]
        else:
            self.components = comps
        self.refresh()

    @staticmethod
    def _normalize(components):
        """Handle edge cases like absolute paths, ".." and variables."""
        from .variables import Variable
        initial_slash = (components and components[0] == '')
        #print 'components =', components
        result = []
        try:
            for c in components:
                if isinstance(c, Variable):
                    result.append(c)
                    continue
                elif c in ('', os.curdir):
                    continue
                if c != os.pardir or (not initial_slash and not result) or \
                   (result and result[-1] == os.pardir):
                    result.append(c)
                elif result:
                    result.pop()
            if c[:2] == ['', '']:
                del c[0]
        except Exception, e:
            getLogger('pyerector.execute').exception(e)
            raise
        else:
            if initial_slash:
                result.insert(0, '')
            #getLogger('pyerector.execute').debug('comp = %s; result = %s', components, result)
        return result

    def refresh(self):
        self.__getstat(self._join())

    def __str__(self):
        return self.value

    def __repr__(self):
        return '<Path (%s) %s>' % (self.type, self.value)

    def _join(self):
        """Return a normalized pathname string, evaluating variables and joining subpaths."""
        from .variables import Variable
        c = []
        for i in self.components:
            while isinstance(i, Variable):
                i = i.value
            else:
                c.append(i)
        d = []
        for i in c:
            if isinstance(i, Path):
                d.extend(i.components)
            else:
                d.append(i)
        value = self.sep.join(d)
        assert isinstance(value, str)
        return os.path.normpath(value)

    @classmethod
    def _split(cls, value):
        """Split a pathname string along the seperator."""
        return value.split(cls.sep)

    def __getstat(self, fname):
        """Load the stat data from the file (inode)."""
        try:
            self.stat = os.lstat(fname)
        except OSError:
            self.stat = None

    @property
    def value(self):
        """Return the string representing the path."""
        value = self._join()
        if self.has_variable:
            self.__getstat(value)
        assert isinstance(value, str)
        return value

    @property
    def basename(self):
        """The basename component of the path, as a Path instance."""
        if len(self.components) > 0:
            return self.__class__(self.components[-1])
        else:
            return self.__class__(os.curdir)

    @property
    def dirname(self):
        """The dirname componment of the path, as a Path instance."""
        return self.__class__(*tuple(self.components[:-1]))

    @property
    def ext(self):
        """The file extension, as a str instance."""
        return os.path.splitext(self.value)[1]

    @property
    def type(self):
        """File type, one of Path.TYPE enum values."""
        self.__getstat(self._join())
        if self.stat is None:
            return self.TYPE.NOENT
        ftype = os.path.stat.S_IFMT(self.stat[os.path.stat.ST_MODE])
        if os.path.stat.S_ISLNK(ftype):
            return self.TYPE.LINK
        elif os.path.stat.S_ISDIR(ftype):
            return self.TYPE.DIR
        elif os.path.stat.S_ISREG(ftype):
            return self.TYPE.FILE
        elif os.path.stat.S_ISFIFO(ftype):
            return self.TYPE.PIPE
        else:
            return self.TYPE.OTHER

    @property
    def mtime(self):
        """Float of the file's modification time, or None if no entry."""
        return self.stat and self.stat[os.path.stat.ST_MTIME] or None
    @property
    def atime(self):
        """Float of the file's access time, or None if no entry."""
        return self.stat and self.stat[os.path.stat.ST_ATIME] or None
    @property
    def ctime(self):
        """Float of the file's change time or None if no entry."""
        return self.stat and self.stat[os.path.stat.ST_CTIME] or None

    @property
    def mode(self):
        """Return permission bits or None if no entry."""
        if self.stat:
            return os.path.stat.S_IMODE(self.stat[os.path.stat.ST_MODE])
        else:
            return None

    @property
    def exists(self):
        """Boolean where True means the file exists."""
        return self.type != self.TYPE.NOENT
    @property
    def isdir(self):
        """Boolean where True means the file is a directory."""
        return self.type == self.TYPE.DIR
    @property
    def islink(self):
        """Boolean where True means the file is a symbolic link."""
        return self.type == self.TYPE.LINK
    @property
    def isfile(self):
        """Boolean where True means the file is a regular file."""
        return self.type == self.TYPE.FILE

    @property
    def isabs(self):
        """Boolean where True is the pathname absolute."""
        return os.path.isabs(self.value)

    @property
    def abs(self):
        """The absolute pathname, as a Path instance."""
        return Path(os.path.abspath(self.value))

    @property
    def real(self):
        """The real pathname (follow symlinks), as a Path instance."""
        return Path(os.path.realpath(self.value))

    def __len__(self):
        """Integer; if a directory, return number of entries,
if a regular file or link, return data size, if no entry, return 0."""
        if self.isdir:
            return len(os.listdir(self.value))
        elif self.isfile or self.islink:
            return self.stat[os.path.stat.ST_SIZE]
        else:
            return 0

    def __iter__(self):
        """If a directory, return the sorted contents as a generator."""
        if self.isdir:
            for entry in sorted(os.listdir(self.value)):
                yield self + entry
        else:
            raise TypeError('expecting a directory')

    def __hash__(self):
        """Return a hash of the expanded pathname."""
        return hash(self.value)

    def __eq__(self, other):
        if isinstance(other, Path):
            return self.value == other.value
        else:
            return self.value == other
    def __lt__(self, other):
        if isinstance(other, Path):
            return self.value < other.value
        else:
            return self.value < other

    def __add__(self, other):
        """Join two pathnames together, as a Path instance."""
        return Path(self, other)

    def __radd__(self, other):
        """Join two pathnames together, as a Path instance."""
        return Path(other, self)

    def __sub__(self, other):
        """Return the relative portion of two pathnames, as a Path instance."""
        return Path(os.path.relpath(str(self), str(other)))

    def __rsub__(self, other):
        """Return the relative portion of two pathnames, as a Path instance."""
        return Path(os.path.relpath(str(other), str(self)))

    def addext(self, ext):
        """Append an extension to the basename, returning a new Path instance."""
        return self.__class__(self.value + ext)
    def delext(self):
        """Remove the extension of the basename, returning a new Path instance."""
        return self.__class__(os.path.splitext(self.value)[0])

    def open(self, mode=None):
        """Return a Python file object; if the file does not exist,
create it, if it is not a file, return an exception."""
        if not self.exists:
            if mode is None:
                mode = 'w'
            elif mode.startswith('r'):
                raise TypeError('expecting file')
            f = open(self.value, mode)
            self.refresh()
            return f
        elif self.isfile:
            if mode is None:
                mode = 'r'
            return open(self.value, mode)
        else:
            raise TypeError('expecting file or no entry')

    # pattern matching

    def match(self, patt, ignorecase=False):
        """Boolean where True when the basename matches the pattern."""
        if ignorecase:
            from fnmatch import fnmatch
        else:
            from fnmatch import fnmatchcase as fnmatch
        try:
            return fnmatch(str(self.basename), patt)
        except IndexError:
            return False

    def glob(self, patt, ignorecase=False):
        return [fn for fn in self if fn.match(patt, ignorecase=ignorecase)]

    # FS operations

    def chmod(self, mode):
        if self.exists:
            os.chmod(self.value, mode)
            self.refresh()

    def remove(self):
        if not self.exists:
            return
        elif self.isdir:
            for entry in self:
                entry.remove()
            os.rmdir(self.value)
        else:
            os.remove(self.value)
        self.refresh()

    def rename(self, other):
        if not self.exists:
            raise TypeError('expecting file')
        if isinstance(other, str):
            other = Path(other)
        os.rename(self.value, other.value)
        self.refresh()
        other.refresh()
        return other

    def utime(self, atime, mtime):
        if not self.exists:
            raise TypeError('expecting file')
        os.uname(self.value, (atime, mtime))
        self.refresh()

    # file operations

    def copy(self, dest):
        from shutil import copy2
        getLogger('pyerector.execute').debug('%s.copy(%s)', repr(self), repr(dest))
        copy2(self.value, dest.value)

    # directory operations

    @classmethod
    def cwd(cls):
        return cls(os.path.abspath(os.curdir))

    def chdir(self):
        if not self.exists:
            import errno
            raise OSError(errno.ENOENT, self.value)
        elif self.isdir:
            os.chdir(self.value)
        else:
            raise TypeError('expecting a directory')
        self.refresh()

    def mkdir(self):
        logger = getLogger('pyerector.execute')
        if not self.exists:
            # recurse upward
            self.dirname.mkdir()
            logger.debug('mkdir(%s)', str(self.value))
            try:
                os.mkdir(self.value)
            except OSError:
                pass
        elif self.isdir:
            return
        else:
            raise TypeError('expecting no entry or directory')
        self.refresh()

    # symlink operations

    def readlink(self):
        if self.islink:
            return Path(os.readlink(self.value))
        else:
            raise TypeError('expecting a symlink')

    def makelink(self, value):
        if isinstance(value, Path):
            value = value.value
        if not self.exists:
            os.symlink(value, self.value)
        elif self.islink:
            os.remove(self.value)
            os.symlink(value, self.value)
        else:
            raise TypeError('entry exists')
        self.refresh()

    # fifo/pipe operations
    def makepipe(self, mode=None):
        if mode is None:
            mode = int('0666', 8)
        if not self.exists:
            os.mkfifo(self.value, mode)
        else:
            raise TypeError('entry exists')
        self.refresh()

homedir = Path(os.environ['HOME'])
rootdir = Path(Path.sep)
