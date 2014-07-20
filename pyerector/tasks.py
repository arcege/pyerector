#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.
"""Define the standard tasks."""

import logging
import os
import shutil
import sys

from .exception import Error
from .helper import Exclusions, Subcommand
from .config import noTimer
from .base import Task, Mapper, Iterator
from .iterators import BasenameMapper, IdentityMapper, FileMapper, \
                       FileIterator, StaticIterator
from .variables import V, VariableSet

# Python 3.x removed the execfile function
try:
    execfile
except NameError:
    from .py3.execfile import execfile

__all__ = [
    'Chmod', 'Copy', 'CopyTree', 'Echo', 'Egg', 'HashGen',
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

    def run(self):
        """Change the permissions on the files."""
        from os import chmod
        mode = self.get_kwarg('mode', int)
        for fname in self.get_files(self.get_args('files')):
            self.asserttype(fname, str, 'files')
            self.logger.info('chmod(%s, %o)', fname, mode)
            chmod(self.join(fname), mode)


class Container(Task):
    """An internal task for subclassing standard classes Tar and Zip."""
    appname = None
    from os import curdir as root
    name = None
    files = ()
    exclude = Exclusions(usedefaults=False)

    def run(self):
        """Gather filenames and put them into the container."""
        name = self.get_kwarg('name', str, noNone=True)
        root = self.join(self.get_kwarg('root', str))
        excludes = self.get_kwarg('exclude', (Exclusions, tuple, list))
        if not isinstance(excludes, Exclusions):
            excludes = Exclusions(excludes)
        self.preop(name, root, excludes)
        toadd = []
        from glob import glob
        queue = list(self.get_args('files'))
        while queue:
            entry = queue[0]
            del queue[0]
            for fname in glob(self.join(root, entry)):
                if excludes.match(fname):  # if true, then ignore
                    pass
                elif os.path.islink(fname) or os.path.isfile(fname):
                    toadd.append(fname)
                elif os.path.isdir(fname):
                    fnames = [os.path.join(fname, f)
                                  for f in os.listdir(fname)]
                    queue.extend(fnames)
        #verbose('toadd =', toadd)
        self.manifest(name, root, toadd)
        self.contain(name, root, toadd)
        self.postop(name, root, toadd)

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

    def run(self):
        """Copy files to a destination directory."""
        dest = self.get_kwarg('dest', str, noNone=False)
        files = self.get_args('files')
        excludes = self.get_kwarg('exclude', (Exclusions, tuple, list))
        if not isinstance(excludes, Exclusions):
            excludes = Exclusions(excludes)
        if len(files) == 1 and dest is None and isinstance(files[0], Mapper):
            fmap = files[0]
        elif len(files) == 1 and dest is not None and not os.path.isdir(dest):
            fmap = IdentityMapper(self.get_files(files), destdir=dest)
        else:
            fmap = FileMapper(self.get_files(files), destdir=dest)
        self.logger.debug('Copy.fmap = %s', vars(fmap))
        for (sname, dname) in fmap:
            #self.logger.error( repr( (sname, dname) ) )
            srcfile = self.join(sname)
            dstfile = self.join(dname)
            if not excludes.match(os.path.basename(sname)):
                if os.path.isfile(dstfile) and fmap.checkpair(srcfile, dstfile):
                    self.logger.debug('uptodate: %s', dstfile)
                else:
                    self.logger.info('copy2(%s, %s)', sname, dname)
                    shutil.copy2(srcfile, dstfile)


class CopyTree(Task):
    """Copy directory tree. Exclude standard hidden files.
constructor arguments:
CopyTree(srcdir=<DIR>, dstdir=<DIR>, exclude=<defaults>)"""
    srcdir = None
    dstdir = None
    exclude = Exclusions()
    excludes = exclude  # deprecated

    def run(self):
        """Copy a tree to a destination."""
        srcdir = self.get_kwarg('srcdir', str, noNone=True)
        dstdir = self.get_kwarg('dstdir', str, noNone=True)
        excludes = self.get_kwarg('exclude', (Exclusions, tuple, list))
        if not isinstance(excludes, Exclusions):
            excludes = Exclusions(excludes)
        if not os.path.exists(self.join(srcdir)):
            raise OSError(2, "No such file or directory: " + srcdir)
        elif not os.path.isdir(self.join(srcdir)):
            raise OSError(20, "Not a directory: " + srcdir)
        copy_t = Copy(noglob=True, exclude=excludes)
        mkdir_t = Mkdir()
        dirs = [os.curdir]
        while dirs:
            tdir = dirs[0]
            del dirs[0]
            if not excludes.match(tdir):
                mkdir_t(self.join(dstdir, tdir))
                for fname in os.listdir(self.join(srcdir, tdir)):
                    if not excludes.match(fname):
                        spath = self.join(srcdir, tdir, fname)
                        dpath = self.join(dstdir, tdir, fname)
                        if os.path.isdir(spath):
                            dirs.append(os.path.join(tdir, fname))
                        else:
                            copy_t(spath, dest=dpath)


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
        self.logger.log(logging.getLevelName('DISPLAY'), text)


class HashGen(Task):
    """Generate file(s) containing md5 or sha1 hash string.
For example, generates foobar.txt.md5 and foobar.txt.sha1 for the
contents of foobar.txt.  By default, generates for both md5 and sha1.
constructor arguments:
HashGen(*files, hashs=('md5', 'sha1'))"""
    files = ()
    hashs = ('md5', 'sha1')

    def run(self):
        """Generate files with checksums inside."""
        from hashlib import md5, sha1
        files = self.get_files(self.get_args('files'))
        hashs = self.get_kwarg('hashs', tuple)
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
                if (os.path.isfile(sname) and
                        not fmap.checkpair(self.join(sname),
                                           self.join(dname))):
                    hashval.update(open(self.join(sname), 'rb').read())
                    self.logger.debug('writing %s', dname)
                    open(self.join(dname), 'wt').write(
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
        if self.java_home and os.path.exists(self.java_home):
            self.java_prog = os.path.join(self.java_home, 'bin', 'java')
        elif os.path.exists(os.path.expanduser(os.path.join('~', 'java'))):
            self.java_prog = os.path.expanduser(
                os.path.join('~', 'java', 'bin', 'java')
            )
        else:
            raise Error("no java program to execute")
        if not os.access(self.java_prog, os.X_OK):
            raise Error("no java program to execute")

    def addprop(self, var, val):
        """Add a Java system property to the list."""
        self.properties.append((var, val))

    def run(self):
        """Call java."""
        from os import environ
        from os.path import pathsep
        jar = self.get_kwarg('jar', str, noNone=True)
        if self.properties:
            sysprop = ['-D%s=%s' % x for x in self.properties]
        else:
            sysprop = ()
        cmd = (self.java_prog,) + tuple(sysprop) + ('-jar', jar,) + \
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

    def run(self):
        """Make directories."""
        files = self.get_files(self.get_args('files'))
        for arg in files:
            self.asserttype(arg, str, 'files')
            self.mkdir(self.join(arg))

    @classmethod
    def mkdir(cls, path):
        """Recursive mkdir."""
        from logging import getLogger
        logger = getLogger('pyerector.execute')
        if os.path.islink(path) or os.path.isfile(path):
            logger.info('remove(%s)', path)
            os.remove(path)
            cls.mkdir(path)
        elif not path:
            pass
        elif not os.path.isdir(path):
            cls.mkdir(os.path.dirname(path))
            logger.info('mkdir(%s)', path)
            os.mkdir(path)


class PyCompile(Task):
    """Compile Python source files.
constructor arguments:
PyCompile(*files, dest=<DIR>, version='2')"""
    files = ()
    dest = None
    version = '2'

    def run(self):
        """Compile Python source files."""
        import py_compile
        fileset = self.get_files(self.get_args('files'))
        if self.version[:1] == sys.version[:1]:  # compile inline
            for fname in fileset:
                self.logger.debug('py_compile.compile(%s)', fname)
                py_compile.compile(self.join(fname))
        else:
            if self.version[:1] == '2':
                cmd = 'python2'
            elif self.version[:1] == '3':
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

    def run(self):
        """Remove a file or directory tree."""
        files = self.get_args('files')
        noglob = self.get_kwarg('noglob', bool)
        excludes = self.get_kwarg('exclude', (Exclusions, list, tuple))
        if isinstance(files, Iterator):
            pass
        elif len(files) == 1 and isinstance(files, Iterator):
            files = files[0]
        elif isinstance(files, (tuple, list)):
            files = FileIterator(*tuple(files), noglob=noglob, exclude=excludes)
        for name in files:
            self.asserttype(name, str, 'files')
            fname = self.join(name)
            if os.path.isfile(fname) or os.path.islink(fname):
                self.logger.info('remove(%s)', fname)
                os.remove(fname)
            elif os.path.isdir(fname):
                self.logger.info('rmtree(%s)', fname)
                shutil.rmtree(fname)


class Shebang(Copy):
    """Replace the shebang string with a specific pathname.
constructor arguments:
Shebang(*files, dest=<DIR>, token='#!', program=<FILE>)"""
    files = ()
    dest = None
    token = '#!'
    program = None

    def run(self):
        """Replace the shebang string with a specific pathname."""
        self.logger.info('starting Shebang')
        program = self.get_kwarg('program', str, noNone=True)
        srcs = self.get_files(self.get_args('files'))
        dest = self.get_kwarg('dest', str)
        try:
            from io import BytesIO as StringIO
        except ImportError:
            from StringIO import StringIO
        for fname in srcs:
            infname = self.join(fname)
            head = infname.replace(fname, '')
            if dest is None:
                outfname = infname
            else:
                outfname = self.join(
                    dest, fname.replace(head, '')
                )
            inf = open(self.join(fname), 'r')
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
            inf = open(outfname, 'w')
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

    def run(self):
        """Spawn a command."""
        infile = self.get_kwarg('infile', str)
        outfile = self.get_kwarg('outfile', str)
        errfile = self.get_kwarg('errfile', str)
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
        idfile = self.get_kwarg('identfile', str)
        if idfile:
            identfile = ('-i', idfile)
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
        dest = self.get_kwarg('dest', str, noNone=True)
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

    def run(self):
        """Call a PyErector program in a different directory."""
        targets = self.get_args('targets')
        prog = self.get_kwarg('prog', str)
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
        cmd = (os.path.join('.', prog),) + tuple(options) + tuple(targets)
        env = self.get_kwarg('env', dict)
        wdir = self.get_kwarg('wdir', str)
        from os import environ
        evname = 'PYERECTOR_PREFIX'
        nevname = os.path.basename(wdir)
        if evname in environ and environ[evname]:
            env[evname] = '%s: %s' % (environ[evname], nevname)
        else:
            env[evname] = nevname
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
    def run(self):
        dest = self.get_kwarg('dest', str)
        files = self.get_args('files')
        excludes = self.get_kwarg('exclude', (Exclusions, tuple, list))
        if not isinstance(excludes, Exclusions):
            excludes = Exclusions(excludes)
        if len(files) == 1 and dest is None and isinstance(files[0], Mapper):
            fmap = files[0]
        elif len(files) == 1 and dest is not None and not os.path.isdir(dest):
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
                if os.path.islink(srcfile) and fmap.checkpair(dstfile, srcfile):
                    self.logger.debug('uptodate: %s', dstfile)
                else:
                    self.logger.info('symlink(%s, %s)', dname, sname)
                    os.symlink(dstfile, srcfile)


class Tar(Container):
    """Generate a 'tar' archive file.
Constructure arguments:
Tar(*files, name=None, root=os.curdir, exclude=(defaults)."""
    def contain(self, name, root, toadd):
        """Add a list of files to the container."""
        import tarfile
        try:
            tfile = tarfile.open(self.join(name), 'w:gz')
        except IOError:
            raise ValueError('no such file or directory: %s' % name)
        else:
            for fname in toadd:
                path = fname.replace(
                    root + os.sep, ''
                )
                self.logger.debug('tar.add(%s, %s)', fname, path)
                tfile.add(self.join(fname), path)
            tfile.close()


class Tokenize(Task):
    """Replace tokens found in tokenmap with their associated values in
each file.
constructor arguments:
Tokenize(*files, dest=None, tokenmap=VariableSet())"""
    files = ()
    dest = None
    tokenmap = VariableSet()

    def update_tokenmap(self):
        """To be overridden."""

    def run(self):
        """Replace tokens found in tokenmap with their associated values."""
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
        files = self.get_args('files')
        mapper = FileMapper(files, destdir=self.get_kwarg('dest', str),
                            iteratorclass=StaticIterator)
        for (sname, dname) in mapper:
            realcontents = open(self.join(sname), 'rt').read()
            alteredcontents = tokens.sub(repltoken, realcontents)
            if alteredcontents != realcontents:
                open(self.join(dname), 'wt').write(alteredcontents)


class Touch(Task):
    """Create file if it didn't exist already.
constructor arguments:
Touch(*files, dest=None)"""
    files = ()
    dest = None

    def run(self):
        from .helper import normjoin
        """Create files, unless they already exist."""
        dest = self.get_kwarg('dest', str)
        for fname in self.get_files(self.get_args('files')):
            self.asserttype(fname, str, 'files')
            if dest is not None:
                fname = normjoin(dest, fname)
            self.logger.info('touch(%s)', fname)
            open(self.join(fname), 'a')

class Unittest(Task):
    """Call Python unit tests found.
constructor arguments:
Unittest(*modules, path=())"""
    modules = ()
    path = ()

    def run(self):
        """Call the 'unit-test.py' script in the package directory with
serialized parameters as the first argument string."""
        bdir = os.path.dirname(__file__)
        sfile = os.path.join(bdir, 'unit-test.py')
        if not os.path.exists(sfile):
            raise Error(self, 'unable to find unittest helper program')
        # create a parameter file with a serialized set of the arguments
        params = repr({
            'modules': tuple(self.get_args('modules')),
            'path': self.path,
            'verbose': bool(self.logger.isEnabledFor(logging.INFO)),
            'quiet': bool(self.logger.isEnabledFor(logging.ERROR)),
        })
        # call python <scriptname> <params>
        Subcommand((sys.executable, sfile, params),
                   wdir=V['basedir'],
                   env={'COVERAGE_PROCESS_START': '/dev/null'})


class Uncontainer(Task):
    """Super-class for Untar and Unzip."""
    name = None
    root = None
    files = ()

    def run(self):
        """Extract members from the container."""
        name = self.get_kwarg('name', str, noNone=True)
        root = self.get_kwarg('root', str)
        self.asserttype(root, str, 'root')
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
        return tarfile.open(self.join(fname), 'r:gz')

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
            contfile.extract(fileinfo, path=(root or ""))


class Unzip(Uncontainer):
    """Extract a 'zip' archive file.
Unzip(*files, name=<tarfilename>, root=None)"""
    def get_file(self, fname):
        """Open the container."""
        from zipfile import ZipFile
        return ZipFile(self.join(fname), 'r')

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
            dname = os.path.join(root, member)
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
            zfile = ZipFile(self.join(name), 'w')
        except IOError:
            raise ValueError('no such file or directory: %s' % name)
        else:
            for fname in toadd:
                path = fname.replace(
                    root + os.sep, ''
                )
                self.logger.debug('zip.add(%s, %s)', fname, path)
                zfile.write(fname, path)
            zfile.close()


class Egg(Zip):
    """Generate an egg file for Python deployments.
Egg(*files, name=<eggfilename>, root=os.curdir, exclude=(defaults))"""
    def manifest(self, name, root, toadd):
        """Generate a manifest structure."""
        if os.path.exists(os.path.join(root, 'setup.py')):
            setupvalue = self.get_setup_py(os.path.join(root, 'setup.py'))
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
        try:
            os.mkdir(os.path.join(root, 'EGG-INFO'))
        except OSError:
            pass
        open(os.path.join(root, 'EGG-INFO', 'PKG-INFO'), 'wt').write(pkg_info)
        for fn in ('dependency_links.txt', 'zip-safe'):
            open(os.path.join(root, 'EGG-INFO', fn), 'wt').write(os.linesep)
        open(os.path.join(root, 'EGG-INFO', 'top_level.txt'), 'wt').write(
            'pyerector' + os.linesep
        )
        open(os.path.join(root, 'EGG-INFO', 'SOURCES.txt'), 'wt').write(
            '\n'.join(sorted([s.replace(root+os.sep, '') for s in toadd]))
        )
        toadd.extend(
            [os.path.join(root, 'EGG-INFO', 'PKG-INFO'),
             os.path.join(root, 'EGG-INFO', 'dependency_links.txt'),
             os.path.join(root, 'EGG-INFO', 'zip-safe'),
             os.path.join(root, 'EGG-INFO', 'top_level.txt'),
             os.path.join(root, 'EGG-INFO', 'SOURCES.txt')
            ]
        )

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
            execfile(filename, mod, mod)
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

