#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.
"""Define the standard tasks."""

import logging
import os
import shutil
import sys

from .exception import Error
from .args import Arguments
from .path import Path
from .helper import Exclusions, Subcommand, DISPLAY
from .config import noTimer
from .base import Initer, Task, Mapper, Iterator
from .iterators import BasenameMapper, IdentityMapper, FileMapper, \
                       FileIterator, StaticIterator
from .variables import V, VariableSet

# Python 3.x removed the execfile function
try:
    execfile
except NameError:
    from .py3.execfile import execfile

__all__ = [
    'Chmod', 'Copy', 'CopyTree', 'Echo', 'Egg', 'EncodeVar', 'HashGen',
    'Java', 'Mkdir', 'PyCompile', 'Remove', 'Scp', 'Shebang', 'Spawn',
    'Ssh', 'SubPyErector', 'Symlink', 'Tar', 'Tokenize', 'Touch',
    'Unittest', 'Untar', 'Unzip', 'Zip',
]


class Chmod(Task):
    """Change file permissions.
constructor arguments:
Chmod(*files, mode=0666)"""
    files = ()
    mode = int('666', 8)  # gets around Python 2.x vs 3.x octal issue

    arguments = Arguments(
        Arguments.List('files', types=(Iterator, Path, str), cast=FileIterator),
        Arguments.Keyword('mode', types=int, default=int('666', 8), cast=int),
    )

    def run(self):
        """Change the permissions on the files."""
        if self.has_arguments:
            files = self.get_files()
            mode = self.args.mode
        else:
            files = self.get_files(self.get_args('files'))
            mode = self.get_kwarg('mode', int)
        for fname in files:
            self.asserttype(fname, (Path, str), 'files')
            self.logger.info('chmod(%s, %o)', fname, mode)
            p = self.join(fname)
            p.chmod(mode)
            if isinstance(fname, Path):
                fname.refresh()


class Container(Task):
    """An internal task for subclassing standard classes Tar and Zip."""
    appname = None
    from os import curdir as root
    name = None
    files = ()
    recurse = True
    fileonly = False
    exclude = Exclusions(usedefaults=False)

    arguments = Arguments(
        Arguments.List('files', types=(Iterator, Path, str), cast=FileIterator),
        Arguments.Keyword('name', types=(Path, str), noNone=True),
        Arguments.Keyword('root', types=(Path, str), default=os.curdir, cast=Path),
    ) + Initer.basearguments

    def run(self):
        """Gather filenames and put them into the container."""
        if self.has_arguments:
            files = self.get_files()
            name = self.args.name
            root = self.args.root
            excludes = self.args.exclude
        else:
            files = self.get_files(self.get_args('files'))
            name = self.get_kwarg('name', (Path, str), noNone=True)
            root = self.join(self.get_kwarg('root', (Path, str)))
            excludes = self.get_kwarg('exclude', (Exclusions, tuple, list))
        if not isinstance(excludes, Exclusions):
            excludes = Exclusions(excludes)
        self.logger.debug('Container.run(name=%s, root=%s, excludes=%s)',
                repr(name), repr(root), repr(excludes))
        self.preop(name, root, excludes)
        toadd = set()
        queue = list(files)
        self.logger.debug('Container.run: files=%s', queue)
        while queue:
            entry = queue[0]
            del queue[0]
            try:
                if isinstance(entry, (Path, str)):
                    self._check_path(Path(entry), toadd, excludes, queue)
                else:
                    if isinstance(entry, Iterator):
                        sequence = iter(entry)
                    else:
                        sequence = root.glob(entry)
                    for fname in sequence:
                        self._check_path(Path(fname), toadd, excludes, queue)
            except TypeError:
                pass
        toadd = sorted(toadd)  # covert set to a list and sort
        self.manifest(name, root, toadd)
        self.contain(name, root, toadd)
        self.postop(name, root, toadd)

    @staticmethod
    def _check_path(fname, toadd, excludes, queue):
        if excludes.match(fname):  # if true, ignore
            pass
        elif fname.islink or fname.isfile:
            toadd.add(fname)
        elif fname.isdir:
            queue.extend(fname)  # expand directory listing

    def preop(self, name, root, excludes):
        """To be overridden."""

    def postop(self, name, root, excludes):
        """To be overridden."""

    def manifest(self, name, root, toadd):
        """To be overridden."""

    def contain(self, name, root, toadd):
        """To be overridden."""


class Copy(Task):
    """Copy files to a destination directory. Exclude standard hidden
files.
constructor arguments:
Copy(*files, dest=<destdir>, exclude=<defaults>)"""
    files = ()
    dest = None
    noglob = False

    arguments = Arguments(
        Arguments.List('files', types=(Iterator, Path, str), cast=FileIterator),
        Arguments.Keyword('dest', types=(Path, str)),
    ) + Initer.basearguments

    def run(self):
        """Copy files to a destination directory."""
        if self.has_arguments:
            self.logger.debug('Copy.run: args=%s', self.args)
            dest = self.args.dest
            files = self.args.files
            excludes = self.args.exclude
        else:
            dest = self.get_kwarg('dest', (Path, str), noNone=False)
            files = self.get_args('files')
            excludes = self.get_kwarg('exclude', (str, Exclusions, tuple, list))
        self.logger.debug('Copy.run: files=%s; dest=%s', repr(files), repr(dest))
        if not isinstance(excludes, Exclusions):
            excludes = Exclusions(excludes)
        if len(files) == 1 and dest is None and isinstance(files[0], Mapper):
            fmap = files[0]
        elif len(files) == 1 and dest is not None and not os.path.isdir(str(dest)):
            fmap = IdentityMapper(self.get_files(files), destdir=dest)
        else:
            fmap = FileMapper(self.get_files(files), destdir=dest)
        self.logger.debug('Copy.fmap = %s', vars(fmap))
        for (sname, dname) in fmap:
            #self.logger.error( repr( (sname, dname) ) )
            self.logger.debug('sname = %s; dname = %s', sname, dname)
            srcfile = self.join(sname)
            dstfile = self.join(dname)
            if not excludes.match(sname):
                if dstfile.isfile and fmap.checkpair(srcfile, dstfile):
                    self.logger.debug('uptodate: %s', dstfile)
                else:
                    self.logger.info('copy2(%s, %s)', sname, dname)
                    srcfile.copy(dstfile)
            else:
                self.logger.debug('ignoring %s to %s', sname, dname)


class CopyTree(Task):
    """Copy directory tree. Exclude standard hidden files.
constructor arguments:
CopyTree(srcdir=<DIR>, dstdir=<DIR>, exclude=<defaults>)"""
    srcdir = None
    dstdir = None
    exclude = Exclusions()
    excludes = exclude  # deprecated

    arguments = Arguments(
        Arguments.Keyword('srcdir', types=(Path, str), noNone=True, cast=Path),
        Arguments.Keyword('dstdir', types=(Path, str), noNone=True, cast=Path),
        Arguments.Exclusions('exclude'),
    )

    def run(self):
        """Copy a tree to a destination."""
        if self.has_arguments:
            srcdir = self.args.srcdir
            dstdir = self.args.dstdir
            excludes = self.args.exclude
        else:
            srcdir = self.join(self.get_kwarg('srcdir', (Path, str), noNone=True))
            dstdir = self.join(self.get_kwarg('dstdir', (Path, str), noNone=True))
            excludes = self.get_kwarg('exclude', (str, Exclusions, tuple, list))
        if not isinstance(excludes, Exclusions):
            excludes = Exclusions(excludes)
        if not srcdir.exists:
            raise OSError(2, "No such file or directory: " + srcdir)
        elif not srcdir.isdir:
            raise OSError(20, "Not a directory: " + srcdir)
        copy_t = Copy(noglob=True, exclude=excludes)
        mkdir_t = Mkdir()
        dirs = [srcdir]
        #print 'CopyTree.dirs =', dirs
        while dirs:
            tdir = dirs.pop(0)
            if not excludes.match(tdir):
                mkdir_t.mkdir(dstdir + (tdir - srcdir))
                for fname in tdir:
                    self.logger.debug('fname = %s', fname)
                    if not excludes.match(fname):
                        dpath = dstdir + (fname - srcdir)
                        self.logger.debug('dpath = %s', dpath)
                        if fname.isdir:
                            dirs.append(fname)
                        else:
                            copy_t(fname, dest=dpath)


class Download(Task):
    """Retrieve contents of URLs.
constructor arguments:
Download(*urls, destdir=DIR)"""
    dest = None
    urls = ()
    def run(self):
        # this is unfinished, it requires a more generic Mapper class
        # than one is available now
        raise NotImplementedError
        """
        import urllib
        from posixpath import basename
        from .iterators import BaseIterator
        urls = self.get_files(self.get_args('urls'))
        urls = BaseIterators(self.get_args('urls'), noglob=True, fileonly=False)

        dest = self.get_kwarg('dest', str)
        if isinstance(urls, str):
            urls = (urls,)
        if isinstance(urls, FileMapper):
            urls = urls
        elif isinstance(dest, str) and os.path.isdir(dest):
            urls = BasenameMapper(urls, destdir=dest,
                                  mapper=lambda x: x or 'index.html')
        elif isinstance(dest, str):
            urls = IdentityMapper(urls, destdir=dest)
        else:
            urls = FileMapper(urls, destdir=dest)
        for url, fname in urls:
            path = urllib.splithost(urllib.splittype(url)[1])[1]
            self.logger.debug('Download.path=%s; Download.fname=%s', path, fname)
            try:
                urllib.urlretrieve(url, filename=fname)
            except Exception, e:
                raise Error(str(self), '%s: unable to retrieve %s' % (e, url))
        """


class Echo(Task):
    """Display a message, arguments are taken as with logger (msg, *args).
This is displayed by the logging module, but at the internal 'DISPLAY'
level created in pyerector.helper."""
    msgs = ()

    def run(self):
        """Display messages."""
        args = self.get_args('msgs')
        if args:
            msg, rest = args[0], args[1:]
            text = msg % rest
        else:
            text = ''
        self.logger.log(DISPLAY, text)


class EncodeVar(Task):
    """Encode a Variable using zlib and base64.
To Decode, use:
def Decode(data):
    from zlib import decompress
    try:
        from base64 import b64decode
    except ImportError:
        from binascii import a2b_base64
        accum = []
        for line in data.rstrip().split('\n'):
            accum.append(a2b_base64(line))
        bdata = ''.join(accum)
    else:
        bdata = b64decode(data)
    return decompress(data)
"""
    source = None
    dest = None

    arguments = Arguments(
        Arguments.Keyword('source'),
        Arguments.Keyword('dest'),
    )

    def run(self):
        """Encode a string."""
        V(self.args.dest).value = self.encode(V(self.args.source).value)

    @staticmethod
    def encode(data):
        """Perform the actual encoding."""
        from zlib import compress
        from base64 import b64encode
        return b64encode(compress(data))


class HashGen(Task):
    """Generate file(s) containing md5 or sha1 hash string.
For example, generates foobar.txt.md5 and foobar.txt.sha1 for the
contents of foobar.txt.  By default, generates for both md5 and sha1.
constructor arguments:
HashGen(*files, hashs=('md5', 'sha1'))"""
    files = ()
    hashs = ('md5', 'sha1')

    def cast(value):
        if isinstance(value, (list, tuple, set)):
            return tuple(value)
        else:
            return str(value)
    arguments = Arguments(
        Arguments.List('files'),
        Arguments.Keyword('hashs', types=(tuple, str), default=('md5', 'sha1'), cast=cast),
    )

    def run(self):
        """Generate files with checksums inside."""
        from hashlib import md5, sha1
        files = self.get_files()
        hashs = self.args.hashs
        self.logger.debug('files = %s; hashs = %s', files, hashs)
        fmaps = []
        if 'md5' in hashs:
            fmaps.append(
                (md5, FileMapper(files, mapper='%(name)s.md5'))
            )
        if 'sha1' in hashs:
            fmaps.append(
                (sha1, FileMapper(files, mapper='%(name)s.sha1'))
            )
        for hashfunc, fmap in fmaps:
            for sname, dname in fmap:
                hashval = hashfunc()
                sname = self.join(sname)
                dname = self.join(dname)
                self.logger.debug('HashGen.run: checkpair(%s, %s) = %s', sname, dname, fmap.checkpair(sname, dname))
                if sname.isfile and not fmap.checkpair(sname, dname):
                    hashval.update(sname.open('rb').read())
                    self.logger.debug('writing %s', dname)
                    dname.open('wt').write(
                            hashval.hexdigest() + '\n'
                    )


class Java(Task):
    """Call a Java routine.
constructor arguments:
Java(jar=<JAR>, java_home=<$JAVA_HOME>, classpath=(), properties=[])"""
    from os import environ
    try:
        java_home = environ['JAVA_HOME']
    except KeyError:
        java_home = None
    classpath = ()
    properties = []
    del environ
    jar = None

    def __init__(self):
        Task.__init__(self)
        if self.java_home and os.path.exists(str(self.java_home)):
            self.java_prog = os.path.join(str(self.java_home), 'bin', 'java')
        elif os.path.exists(os.path.expanduser(os.path.join('~', 'java'))):
            self.java_prog = os.path.expanduser(
                os.path.join('~', 'java', 'bin', 'java')
            )
        else:
            raise Error("no java program to execute")
        if not os.access(str(self.java_prog), os.X_OK):
            raise Error("no java program to execute")

    def addprop(self, var, val):
        """Add a Java system property to the list."""
        self.properties.append((var, val))

    def run(self):
        """Call java."""
        from os import environ
        from os.path import pathsep
        jar = self.get_kwarg('jar', (Path, str), noNone=True)
        if self.properties:
            sysprop = ['-D%s=%s' % x for x in self.properties]
        else:
            sysprop = ()
        cmd = (self.java_prog,) + tuple(sysprop) + \
            ('-jar', str(jar),) + \
            tuple([str(s) for s in self.args])
        env = environ.copy()
        if self.classpath:
            env['CLASSPATH'] = pathsep.join(self.classpath)
        proc = Subcommand(cmd)
        if proc.returncode:
            raise Error(self, '%s failed with returncode %d' %
                        (self.__class__.__name__.lower(), proc.returncode)
                        )


class Mkdir(Task):
    """Recursively create directories.
constructor arguments:
Mkdir(*files)"""
    files = ()
    noglob = True

    arguments = Arguments(
        Arguments.List('files', types=(Path, str, Iterator), cast=FileIterator),
    ) + Initer.basearguments

    def run(self):
        """Make directories."""
        files = self.get_files()
        self.logger.debug('files = %s: %s', repr(files), vars(files))
        for arg in files:
            self.logger.debug('arg = %s', repr(arg))
            self.asserttype(arg, (Path, str), 'files')
            self.mkdir(self.join(arg))

    @classmethod
    def mkdir(cls, path):
        """Recursive mkdir."""
        # a class method, so we need to get the logger explicitly
        from logging import getLogger
        logger = getLogger('pyerector.execute')
        if isinstance(path, str):
            path = Path(path)
        if path.islink or path.isfile:
            logger.info('remove(%s)', path)
            path.remove()
            path.mkdir()
        elif path.isdir:
            logger.debug('ignoring(%s)', path)
        elif not path.exists:
            #logger.info('mkdir(%s)', path)
            path.mkdir()


class PyCompile(Task):
    """Compile Python source files.
constructor arguments:
PyCompile(*files, dest=<DIR>, version='2')"""
    files = ()
    version = '2'

    arguments = Arguments(
        Arguments.List('files', types=(Iterator, Path, str), cast=FileIterator),
        Arguments.Keyword('version', default='2'),
    )

    def run(self):
        """Compile Python source files."""
        import py_compile
        if self.has_arguments:
            fileset = self.get_files()
            version = self.args.version
        else:
            fileset = self.get_files(self.get_args('files'))
            version = self.version
        if version[:1] == sys.version[:1]:  # compile inline
            for fname in fileset:
                self.logger.debug('py_compile.compile(%s)', fname)
                py_compile.compile(str(self.join(fname)))
        else:
            if version[:1] == '2':
                cmd = 'python2'
            elif version[:1] == '3':
                cmd = 'python3'
            else:
                cmd = 'python'
            cmdp = (
                cmd, '-c',
                'import sys; from py_compile import compile; ' +
                '[compile(s) for s in sys.argv[1:]]'
            ) + tuple([self.join(s) for s in fileset])
            try:
                proc = Subcommand(cmdp)
            except Error:
                exc = sys.exc_info()[1]
                if exc.args[0] == 'ENOENT':
                    self.logger.error('%s: Error with %s: %s',
                        self.__class__.__name__, cmd, exc.args[1]
                    )
                else:
                    raise
            else:
                if proc.returncode != 0:
                    self.logger.info('could not compile files with %s', cmd)


class Remove(Task):
    """Remove a file or directory tree.
constructor arguments:
Remove(*files)"""
    files = ()
    noglob = False
    exclude = None

    arguments = Arguments(
        Arguments.List('files', types=(Iterator, Path, str), cast=FileIterator),
    ) + Initer.basearguments

    def run(self):
        """Remove a file or directory tree."""
        if self.has_arguments:
            files = self.get_files()
        else:
            files = self.get_args('files')
            noglob = self.get_kwarg('noglob', bool)
            excludes = self.get_kwarg('exclude', (str, Exclusions, list, tuple))
        if isinstance(files, Iterator):
            pass
        elif len(files) == 1 and isinstance(files, Iterator):
            files = files[0]
        elif isinstance(files, (tuple, list)):
            files = FileIterator(*tuple(files), noglob=noglob, exclude=excludes)
        for name in files:
            self.asserttype(name, (Path, str), 'files')
            fname = self.join(name)
            self.logger.info('remove(%s)', fname)
            fname.remove()


class Shebang(Copy):
    """Replace the shebang string with a specific pathname.
constructor arguments:
Shebang(*files, dest=<DIR>, token='#!', program=<FILE>)"""
    files = ()
    dest = None
    program = None
    token = '#!'

    arguments = Arguments(
        Arguments.List('files', types=(Iterator, Path, str), cast=FileIterator),
        Arguments.Keyword('dest', types=(Path, str), cast=Path),
        Arguments.Keyword('program', types=(Path, str), noNone=True),
    )
    def run(self):
        """Replace the shebang string with a specific pathname."""
        self.logger.info('starting Shebang')
        if self.has_arguments:
            program = self.args.program
            srcs = self.get_files()
            dest = self.args.dest
        else:
            program = self.get_kwarg('program', (Path, str), noNone=True)
            srcs = self.get_files(self.get_args('files'))
            dest = self.get_kwarg('dest', (Path, str))
        try:
            from io import BytesIO as StringIO
        except ImportError:
            from StringIO import StringIO
        for fname in srcs:
            if dest is None:
                outfname = infname
            else:
                outfname = Path(dest, fname.basename)
            inf = infile.open()
            outf = StringIO()
            first = inf.readline()
            if first.startswith(self.token):
                if ' ' in first:
                    wsp = first.find(' ')
                else:
                    wsp = first.find(os.linesep)
                first = first.replace(first[len(self.token):wsp], program)
                outf.write(first)
            else:
                outf.write(first)
            shutil.copyfileobj(inf, outf)
            inf.close()
            outf.seek(0)
            inf = outfname.open('w')
            shutil.copyfileobj(outf, inf)


class Spawn(Task):
    """Spawn a command.
constructor arguments:
Spawn(*cmd, infile=None, outfile=None, errfile=None, env={})"""
    cmd = ()
    infile = None
    outfile = None
    errfile = None
    env = {}

    arguments = Arguments(
        Arguments.List('cmd', types=(tuple, list), cast=tuple),
        Arguments.Keyword('infile', types=(Path, str)),
        Arguments.Keyword('outfile', types=(Path, str)),
        Arguments.Keyword('errfile', types=(Path, str)),
        Arguments.Keyword('env', types=(tuple, dict), default={}, cast=dict),
    )

    def run(self):
        """Spawn a command."""
        if self.has_arguments:
            cmd = self.args.cmd
            infile = self.args.infile
            outfile = self.args.outfile
            errfile = self.args.errfile
            env = self.args.env
        else:
            infile = self.get_kwarg('infile', (Path, str))
            outfile = self.get_kwarg('outfile', (Path, str))
            errfile = self.get_kwarg('errfile', (Path, str))
            infile = infile and self.join(infile) or None
            outfile = outfile and self.join(outfile) or None
            errfile = errfile and self.join(errfile) or None
            env = self.get_kwarg('env', dict)
            cmd = self.get_args('cmd')
        proc = Subcommand(cmd, env=env,
                          stdin=infile, stdout=outfile, stderr=errfile,
                          )
        if proc.returncode < 0:
            raise Error('Subcommand', '%s signal %d raised' %
                            (str(self), abs(proc.returncode)))
        elif proc.returncode > 0:
            raise Error('Subcommand', '%s returned error = %d' %
                            (str(self), proc.returncode))

class SshEngine(Task):
    """Superclass for Scp and Ssh since there is the same basic logic."""
    _cmdprog = None
    host = None
    user = None
    identfile = None
    @property
    def remhost(self):
        ruser = ''
        host = self.get_kwarg('host', str, noNone=True)
        user = self.get_kwarg('user', str)
        if '@' in host:
            ruser, host = host.split('@', 1)
        if user:
            return '%s@%s' % (user, host)
        elif not user and ruser:
            return '%s@%s' % (ruser, host)
        else:
            return host
    def gencmd(self):
        idfile = self.get_kwarg('identfile', (Path, str))
        if idfile:
            identfile = ('-i', str(idfile))
        else:
            identfile = ()
        return (
            self._cmdprog,
            '-o', 'BatchMode=yes',
            '-o', 'ConnectTimeout=10',
            '-o', 'ForwardAgent=no',
            '-o', 'ForwardX11=no',
            '-o', 'GSSAPIAuthentication=no',
            '-o', 'LogLevel=ERROR',
            '-o', 'PasswordAuthentication=no',
            '-o', 'StrictHostkeyChecking=no',
        ) + identfile
    def _run(self, cmd):
        self.logger.debug('ssh.cmd = %s', cmd)
        proc = Subcommand(cmd,
                          stdout=Subcommand.PIPE,
                          stderr=Subcommand.PIPE,
                          wait=True)
        if proc.returncode:
            raise Error(str(self), proc.stderr.read().rstrip())
        else:
            return proc.stdout.read().rstrip()

class Scp(SshEngine):
    """Spawn an scp command.
constructor arguments:
Scp(*files, dest=<dir>, host=<hostname>, user=<username>, identfile=<filename>,
    recurse=bool, down=bool)"""
    _cmdprog = 'scp'
    files = ()
    dest = None
    recurse = False
    down=True

    def remfile(self, filename):
        return '%s:%s' % (self.remhost, filename)
    def lclfile(self, filename):
        return self.join(filename)
    def run(self):
        recurse = self.get_kwarg('recurse', bool)
        dest = self.get_kwarg('dest', (Path, str), noNone=True)
        down = self.get_kwarg('down', bool)
        files = self.get_args('files')
        if down:
            left, right = self.remfile, self.lclfile
        else:
            left, right = self.lclfile, self.remfile
        cmd = self.gencmd()
        if recurse:
            cmd += ('-r',)
        filelst = ()
        for fname in files:
            filelst += (left(fname),)
        filelst += (right(dest),)
        self.logger.info('%s%s', self, filelst)
        self._run(cmd + filelst)

class Ssh(SshEngine):
    """Spawn an ssh command and display the response in verbose mode.
constructor arguments:
Ssh(*cmd, host=<hostname>, user=<username>, identfile=<filename>)
"""
    _cmdprog = 'ssh'
    cmd = ()
    def run(self):
        usercmd = self.get_args('cmd')
        cmd = self.gencmd() + ('-T', self.remhost) + usercmd
        self.logger.info('%s%s', self, usercmd)
        response = self._run(cmd)
        #self.logger.info('Output from %s\n%s', usercmd, response)
        self.logger.warning('\t' + response.rstrip().replace('\n', '\n\t'))

class SubPyErector(Task):
    """Call a PyErector program in a different directory.
constructor arguments:
SubPyErector(*targets, wdir=None, prog='pyerect', env={})
Adds PYERECTOR_PREFIX environment variable."""
    targets = ()
    prog = 'pyerect'
    wdir = None
    env = {}

    arguments = Arguments(
        Arguments.List('targets'),
        Arguments.Keyword('prog', types=(Path, str), default=Path('pyerect'), cast=Path),
        Arguments.Keyword('wdir', types=(Path, str), cast=Path),
        Arguments.Keyword('env', types=(tuple, dict), default={}, cast=dict),
    )

    def run(self):
        """Call a PyErector program in a different directory."""
        if self.has_arguments:
            targets = self.args.targets
            prog = self.args.prog
            wdir = self.args.wdir
            env = self.args.env
        else:
            targets = self.get_args('targets')
            prog = self.get_kwarg('prog', (Path, str))
            env = self.get_kwarg('env', dict)
            wdir = self.get_kwarg('wdir', (Path, str))
        # we explicitly add './' to prevent searching PATH
        options = []
        logger = logging.getLogger('pyerector')
        if logger.isEnabledFor(logging.DEBUG):
            options.append('--DEBUG')
        elif logger.isEnabledFor(logging.INFO):
            options.append('--verbose')
        elif logger.isEnabledFor(logging.ERROR):
            options.append('--quiet')
        if noTimer:
            options.append('--timer')
        relprog = Path() + prog.basename
        cmd = (str(relprog),) + tuple(options) + targets
        from os import environ
        evname = 'PYERECTOR_PREFIX'
        nevname = Path(wdir).basename
        if evname in environ and environ[evname]:
            env[evname] = '%s: %s' % (environ[evname], str(nevname))
        else:
            env[evname] = str(nevname)
        rc = Subcommand(cmd, wdir=wdir, env=env, wait=True)
        if rc.returncode < 0:
            raise Error('SubPyErector', '%s signal %d raised' %
                            (str(self), abs(rc.returncode)))
        elif rc.returncode > 0:
            raise Error('SubPyErector', '%s returned error = %d' %
                            (str(self), rc.returncode))

class Symlink(Task):
    """Generate a symbolic link.
constructor arguments:
Symlink(*files, dest=<dest>, exclude=<defaults>)"""
    files = ()
    dest = None
    exclude = None

    arguments = Arguments(
        Arguments.List('files', types=(Iterator, Path, str), cast=FileIterator),
        Arguments.Keyword('dest', types=(Path, str), cast=Path),
        Arguments.Exclusions('exclude'),
    ) + Initer.basearguments

    def run(self):
        if self.has_arguments:
            files = self.get_files()
            dest = self.args.dest
            excludes = self.args.excludes
        else:
            dest = Path(self.get_kwarg('dest', (Path, str)))
            files = self.get_args('files')
            excludes = self.get_kwarg('exclude', (Exclusions, tuple, list))
        if not isinstance(excludes, Exclusions):
            excludes = Exclusions(excludes)
        if len(files) == 1 and dest is None and isinstance(files[0], Mapper):
            fmap = files[0]
        elif len(files) == 1 and dest is not None and not dest.isdir:
            fmap = FileMapper(files[0], destdir=dest, exclude=excludes)
        elif dest is not None:
            fmap = FileMapper(self.get_files(files),
                              destdir=dest, exclude=excludes)
        else:
            raise Error('must supply dest to %s' % self)
        for (sname, dname) in fmap:
            self.logger.debug('symlink.sname=%s; symlink.dname=%s', sname, dname)
            srcfile = self.join(sname)
            dstfile = self.join(dname)
            if not excludes.match(sname):
                if srcfile.islink and fmap.checkpair(dstfile, srcfile):
                    self.logger.debug('uptodate: %s', dstfile)
                else:
                    self.logger.info('symlink(%s, %s)', dname, sname)
                    dstfile.makelink(srcfile)


class Tar(Container):
    """Generate a 'tar' archive file.
Constructure arguments:
Tar(*files, name=None, root=os.curdir, exclude=(defaults)."""
    def contain(self, name, root, toadd):
        """Add a list of files to the container."""
        import tarfile
        try:
            tfile = tarfile.open(str(self.join(name)), 'w:gz')
        except IOError:
            raise ValueError('no such file or directory: %s' % name)
        else:
            for fname in toadd:
                if isinstance(fname, Path):
                    path = fname - root
                else:
                    path = Path(fname) - root
                self.logger.debug('tar.add(%s, %s)', fname, path)
                tfile.add(str(self.join(fname)), str(path))
            tfile.close()


class Tokenize(Task):
    """Replace tokens found in tokenmap with their associated values in
each file.
constructor arguments:
Tokenize(*files, dest=None, tokenmap=VariableSet())"""
    files = ()
    dest = None
    tokenmap = VariableSet()

    arguments = Arguments(
        Arguments.List('files', types=(Iterator, Path, str), cast=FileIterator),
        Arguments.Keyword('dest', types=(Path, str), cast=Path),
        Arguments.Keyword('tokenmap', types=VariableSet, default=VariableSet()),
    )

    def update_tokenmap(self):
        """To be overridden."""

    def run(self):
        """Replace tokens found in tokenmap with their associated values."""
        if self.has_arguments:
            files = self.get_files()
            dest = self.args.dest
            tokenmap = self.args.tokenmap
        else:
            files = self.get_args('files')
            dest = self.get_kwarg('dest', (Path, str))
            tokenmap = self.get_kwarg('tokenmap', VariableSet)
            if not isinstance(tokenmap, VariableSet):
                raise TypeError('tokenmap must be a VariableSet instance')
        self.update_tokenmap()
        import re

        def repltoken(match, tmap=tokenmap):
            """Replace."""
            self.logger.debug('found %s', match.group(0))
            result = tmap.get(match.group(0))
            return result is not None and str(result) or ''

        def quote(string):
            """Quote special characters."""
            return string.replace('\\', r'\\').replace('.', r'\.')\
                         .replace('$', r'\$').replace('(', r'\(')\
                         .replace(')', r'\)').replace('|', r'\|')
        patt = '|'.join(
            [quote(k) for k in tokenmap]
        )
        tokens = re.compile(r'(%s)' % patt, re.MULTILINE)
        self.logger.debug('patt = %s', str(tokens.pattern))
        mapper = FileMapper(files, destdir=dest,
                            iteratorclass=StaticIterator)
        for (sname, dname) in mapper:
            try:
                realcontents = self.join(sname).open('rt').read()
            except TypeError, e:
                raise Error('%s: %s' % (sname, e))
            alteredcontents = tokens.sub(repltoken, realcontents)
            if alteredcontents != realcontents:
                self.join(dname).open('wt').write(alteredcontents)


class Touch(Task):
    """Create file if it didn't exist already.
constructor arguments:
Touch(*files, dest=None)"""
    files = ()
    dest = None

    arguments = Arguments(
        Arguments.List('files', types=(Iterator, Path, str), cast=FileIterator),
        Arguments.Keyword('dest', types=(Path, str), cast=Path),
    )

    def run(self):
        from .helper import normjoin
        """Create files, unless they already exist."""
        if self.has_arguments:
            files = self.get_files()
            dest = self.args.dest
        else:
            files = self.get_files(self.get_args('files'))
            dest = Path(self.get_kwarg('dest', (Path, str)))
        for fname in files:
            #self.asserttype(fname, (Path, str), 'files')
            if dest is not None:
                fname = dest + fname
            self.logger.info('touch(%s)', fname)
            self.join(fname).open('a')

class Unittest(Task):
    """Call Python unit tests found.
constructor arguments:
Unittest(*modules, path=())"""
    modules = ()
    path = ()

    arguments = Arguments(
        Arguments.List('modules', types=(Path, str), cast=str),
    )

    def run(self):
        """Call the 'unit-test.py' script in the package directory with
serialized parameters as the first argument string."""
        if self.has_arguments:
            modules = self.args.modules
        else:
            modules = tuple(self.get_args('modules'))
        bdir = Path(__file__).dirname
        sfile = bdir + 'unit-test.py'
        if not sfile.exists:
            raise Error(self, 'unable to find unittest helper program')
        # create a parameter file with a serialized set of the arguments
        params = repr({
            'modules': modules,
            'path': self.path,
            'verbose': bool(self.logger.isEnabledFor(logging.INFO)),
            'quiet': bool(self.logger.isEnabledFor(logging.ERROR)),
        })
        # call python <scriptname> <params>
        Subcommand((sys.executable, str(sfile), params),
                   wdir=V['basedir'],
                   env={'COVERAGE_PROCESS_START': '/dev/null'})


class Uncontainer(Task):
    """Super-class for Untar and Unzip."""
    name = None
    root = None
    files = ()

    arguments = Arguments(
        Arguments.List('files', types=(Iterator, Path, str), cast=FileIterator),
        Arguments.Keyword('name', types=(Path, str), noNone=True),
        Arguments.Keyword('root', types=(Path, str)),
    )

    def run(self):
        """Extract members from the container."""
        if self.has_arguments:
            files = self.get_files()
            name = self.args.name
            root = self.args.root
        else:
            name = self.get_kwarg('name', (Path, str), noNone=True)
            root = self.get_kwarg('root', (Path, str))
            files = self.get_args('files')
        try:
            contfile = self.get_file(name)
        except IOError:
            raise ValueError('no such file or directory: %s' % name)
        else:
            fileset = self.retrieve_members(contfile, files)
            self.extract_members(contfile, fileset, root)
            contfile.close()

    def get_file(self, name):
        """To be overridden."""
        return None

    def extract_members(self, contfile, fileset, root):
        """To be overridden."""

    @staticmethod
    def retrieve_members(contfile, files):
        """To be overridden."""
        return None


class Untar(Uncontainer):
    """Extract a 'tar' archive file.
Untar(*files, name=<tarfilename>, root=None)"""
    def get_file(self, fname):
        """Open the container."""
        import tarfile
        return tarfile.open(str(self.join(fname)), 'r:gz')

    @staticmethod
    def retrieve_members(contfile, files):
        """Retrieve the members from the container."""
        fileset = []
        files = tuple(files)  # needed for contents test
        for member in contfile.getmembers():
            if (member.name.startswith(os.sep) or
                    member.name.startswith(os.pardir)):
                pass
            elif not files or member.name in files:
                fileset.append(member)
        return fileset

    def extract_members(self, contfile, fileset, root):
        """Extract members from the container."""
        for fileinfo in fileset:
            self.logger.debug('tar.extract(%s)', fileinfo.name)
            contfile.extract(fileinfo, path=(str(root) or ""))


class Unzip(Uncontainer):
    """Extract a 'zip' archive file.
Unzip(*files, name=<tarfilename>, root=None)"""
    def get_file(self, fname):
        """Open the container."""
        from zipfile import ZipFile
        return ZipFile(str(self.join(fname)), 'r')

    @staticmethod
    def retrieve_members(contfile, files):
        """Retrieve the members from the container."""
        fileset = []
        files = tuple(files)  # needed for contents test
        for member in contfile.namelist():
            if member.startswith(os.sep) or member.startswith(os.pardir):
                pass
            elif not files or member in files:
                fileset.append(member)
        return fileset

    def extract_members(self, contfile, fileset, root):
        """Extract members from the container."""
        for member in fileset:
            dname = os.path.join(str(root), member)
            Mkdir.mkdir(os.path.dirname(dname))
            self.logger.debug('zip.extract(%s)', member)
            dfile = open(dname, 'wb')
            dfile.write(contfile.read(member))


class Zip(Container):
    """Generate a 'zip' archive file.
Zip(*files, name=(containername), root=os.curdir, exclude=(defaults)."""
    def contain(self, name, root, toadd):
        """Add the files to the container."""
        from zipfile import ZipFile
        try:
            self.logger.debug('Zip.contain(name=%s, root=%s, toadd=%s)',
                    repr(name), repr(root), repr(toadd))
            zfile = ZipFile(str(self.join(name)), 'w')
        except IOError:
            raise ValueError('no such file or directory: %s' % name)
        else:
            for fname in toadd:
                path = str(fname - root)
                self.logger.debug('zip.add(%s, %s)', fname, path)
                zfile.write(str(fname), path)
            zfile.close()


class Egg(Zip):
    """Generate an egg file for Python deployments.
Egg(*files, name=<eggfilename>, root=os.curdir, exclude=(defaults))"""
    def manifest(self, name, root, toadd):
        """Generate a manifest structure."""
        fname = Path(name).basename
        fname.delext()
        p = str(fname).find('-')
        if p != -1:
            fname = Path(str(fname)[:p])
        eggdir = root + 'EGG-INFO'
        try:
            eggdir.mkdir()
        except OSError:
            pass
        self.do_file_pkginfo(eggdir, toadd, root)
        self.do_file_dummy(eggdir, toadd, 'dependency_links.txt')
        self.do_file_dummy(eggdir, toadd, 'zip-safe')
        self.do_file_top_level(eggdir, toadd, fname)
        self.do_file_sources(eggdir, toadd, root)

    @staticmethod
    def add_path(seq, path):
        if path not in seq:
            seq.append(path)

    def do_file_dummy(self, rootdir, toadd, fname):
        fn = rootdir + fname
        fn.open('wt').write(os.linesep)
        self.add_path(toadd, fn)
    def do_file_top_level(self, rootdir, toadd, name):
        fn = rootdir + 'top_level.txt'
        fn.open('wt').write(str(name) + os.linesep)
        self.add_path(toadd, fn)
    def do_file_sources(self, rootdir, toadd, root):
        fn = rootdir + 'SOURCES.txt'
        with fn.open('wt') as f:
            for s in sorted([s - root for s in toadd]):
                if s.basename != 'EGG-INFO':
                    f.write(str(s) + os.linesep)
        self.add_path(toadd, fn)
    def do_file_pkginfo(self, rootdir, toadd, root):
        fn = root + 'setup.py'
        if fn.exists:
            setupvalue = self.get_setup_py(fn)
        else:
            raise Error('Egg', 'unable to find a setup.py file')
        pkg_data = {
            'classifiers': '',
        }
        for key in sorted(setupvalue):
            if key == 'classifiers':
                pkg_data[key] = '\n'.join(
                    ['Classifier: %s' % c for c in setupvalue[key]]
                )
            else:
                pkg_data[key] = setupvalue[key]
        pkg_info = '''\
Metadata-Version: 1.1
Name: %(name)s
Version: %(version)s
Summary: %(description)s
Home-page: %(url)s
Author: %(author)s
Author-email: %(author_email)s
License: %(license)s
Download-URL: %(download_url)s
Description: %(long_description)s
Platform: UNKNOWN
%(classifiers)s
''' % pkg_data
        eggdir = root + 'EGG-INFO'
        try:
            eggdir.mkdir()
        except OSError:
            pass
        fname = eggdir + 'PKG-INFO'
        fname.open('wt').write(pkg_info)
        if fname not in toadd:
            toadd.append(fname)
        for fn in ('depenency_links.txt', 'zip-safe'):
            fname = eggdir + fn
            fname.open('wt').write(os.linesep)
            if fname not in toadd:
                toadd.append(fname)
        fname = eggdir + 'top_level.txt'
        fname.open('wt').write('pyerector' + os.linesep)
        if fname not in toadd:
            toadd.append(fname)
        fname = eggdir + 'SOURCES.txt'
        fname.open('wt').write(
            os.linesep.join(sorted(
                [str(s - root) for s in toadd
                    if s.basename != 'EGG-INFO']
            )) + os.linesep
        )
        if fname not in toadd:
            toadd.append(fname)
        # convert Path instances to a str
        toadd[:] = [str(f) for f in toadd]

    @staticmethod
    def get_setup_py(filename):
        """Simulate setup() in a fake distutils and setuptools."""
        import imp
        backups = {}
        script = '''
def setup(**kwargs):
    global myvalue
    myvalue = dict(kwargs)
'''
        code = compile(script, 'setuptools.py', 'exec')
        try:
            for modname in ('setuptools', 'distutils'):
                if modname in sys.modules:
                    backups[modname] = sys.modules[modname]
                else:
                    backups[modname] = None
                mod = sys.modules[modname] = imp.new_module(modname)
                exec(code, mod.__dict__, mod.__dict__)
            mod = {'__builtins__': __builtins__, 'myvalue': None}
            execfile(str(filename), mod, mod)
            for modname in ('setuptools', 'distutils'):
                if sys.modules[modname].myvalue is not None:
                    return sys.modules[modname].myvalue
            else:
                return None
        finally:
            for modname in backups:
                if backups[modname] is None:
                    del sys.modules[modname]
                else:
                    sys.modules[modname] = backups[modname]

