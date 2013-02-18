#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import os
import shutil

from .exception import Error
from .base import Task, Uptodate
from . import debug, verbose

__all__ = [
    'Spawn', 'Remove', 'Copy', 'Shebang', 'CopyTree', 'Mkdir',
    'Chmod', 'Tar', 'Untar', 'Zip', 'Unzip', 'Java', 'Unittest',
]

class Spawn(Task):
    cmd = ()
    infile = None
    outfile = None
    errfile = None
    env = {}
    def run(self):
        infile = self.get_kwarg('infile', str)
        outfile = self.get_kwarg('outfile', str)
        errfile = self.get_kwarg('errfile', str)
        env = self.get_kwarg('env', dict)
        cmd = self.get_args('cmd')
        try:
            from subprocess import call
            realenv = os.environ.copy()
            realenv.update(env)
            if (len(cmd) == 1 and
                (isinstance(cmd, tuple) or isinstance(cmd, list))):
                cmd = tuple(cmd[0])
            else:
                cmd = tuple(cmd)
            ifl = of = ef = None
            if infile:
                ifl = open(infile, 'r')
            if outfile:
                of = open(outfile, 'w')
            if errfile == outfile:
                ef = of
            elif errfile:
                ef = open(errfile, 'w')
            verbose('spawn("' + str(cmd) + '")')
            shellval = not isinstance(cmd, tuple)
            rc = call(cmd, shell=shellval, stdin=ifl, stdout=of, stderr=ef,
                      bufsize=0, env=realenv)
            if rc < 0:
                raise Error(str(self), 'signal ' + str(abs(rc)) + 'raised')
            elif rc > 0:
                raise Error(str(self), 'returned error + ' + str(rc))
            pass
        except ImportError:
            from popen2 import Popen3
            if isinstance(cmd, tuple) or isinstance(cmd, list):
                pcmd = ' '.join('"%s"' % str(s) for s in cmd)
            else:
                pcmd = cmd
            if outfile:
                pcmd += (' >"%s"' % outfile)
            if errfile == outfile:
                pcmd += ' 2>&1'
            elif errfile:
                pcmd += (' 2>"%s"' % errfile)
            verbose('spawn("' + str(pcmd) + '")')
            oldenv = {}
            for ename in env:
                if ename in os.environ:
                    oldenv[ename] = environ[ename]
                else:
                    oldenv[ename] = None
                environ[ename] = env[ename]
            rc = Popen3(pcmd, capturestderr=False, bufsize=0).wait()
            if hasattr(os, 'WIFSIGNALED') and os.WIFSIGNALED(rc):
                raise Error(str(self),
                                 'signal ' + str(os.WTERMSIG(rc)) + 'raised')
            elif os.WEXITSTATUS(rc):
                raise Error(str(self), 'returned error = ' + str(rc))
            for ename in env:
                if oldenv[ename] is None:
                    del environ[ename]
                else:
                    environ[ename] = oldenv[ename]

class Remove(Task):
    files = ()
    noglob = False
    def run(self):
        for fname in self.get_files(self.get_args('files'), self.noglob):
            self.asserttype(fname, str, 'files')
            if os.path.isfile(fname) or os.path.islink(fname):
                verbose('remove(' + str(fname) + ')')
                os.remove(fname)
            elif os.path.isdir(fname):
                verbose('rmtree(' + str(fname) + ')')
                shutil.rmtree(fname)

class Copy(Task):
    files = ()
    dest = None
    noglob = False
    def wantnoglob(self):
        return ((hasattr(self, 'kwargs') and 'noglob' in self.kwargs and self.kwargs['noglob']) or
                self.noglob)
    def run(self):
        #verbose('starting', self.__class__.__name__)
        dest = self.get_kwarg('dest', str, noNone=True)
        srcs = self.get_files(self.get_args('files'), noglob=self.wantnoglob())
        for sname in srcs:
            self.asserttype(sname, str, 'files')
            dname = os.path.join(dest, sname)
            srcfile = self.join(sname)
            dstfile = self.join(dname)
            if os.path.isfile(dstfile) and \
                    Uptodate.checkpair(srcfile, dstfile):
                debug('uptodate:', dstfile)
            else:
                verbose('copy2(' + str(sname) + ', ' + str(dname) + ')')
                shutil.copy2(srcfile, dstfile)

class Shebang(Copy):
    files = ()
    token = '#!'
    def run(self):
        verbose('starting Shebang')
        program = self.get_kwarg('program', str, noNone=True)
        srcs = self.get_files(self.get_args('files'), noglob=self.wantnoglob())
        try:
            from io import BytesIO as StringIO
        except ImportError:
            from StringIO import StringIO
        for fname in srcs:
            inf = open(self.join(fname), 'r')
            outf = StringIO()
            first = inf.readline()
            if first.startswith(self.token):
                if ' ' in first:
                    w = first.find(' ')
                else:
                    w = first.find(os.linesep)
                first = first.replace(first[len(self.token):w], program)
                outf.write(first)
            else:
                outf.write(first)
            copyfileobj(inf, outf)
            inf.close()
            outf.seek(0)
            inf = open(self.join(fname), 'w')
            shutil.copyfileobj(outf, inf)

class CopyTree(Task):
    srcdir = None
    dstdir = None
    excludes = ('.git', '.hg', '.svn')
    def run(self):
        from fnmatch import fnmatch
        srcdir = self.get_kwarg('srcdir', str, noNone=True)
        dstdir = self.get_kwarg('dstdir', str, noNone=True)
        if not os.path.exists(self.join(srcdir)):
            raise OSError(2, "No such file or directory: " + srcdir)
        elif not os.path.isdir(self.join(srcdir)):
            raise OSError(20, "Not a directory: " + srcdir)
        copy_t = Copy(noglob=True)
        mkdir_t = Mkdir()
        dirs = [os.curdir]
        while dirs:
            dir = dirs[0]
            del dirs[0]
            if self.check_exclusion(dir):
                mkdir_t(self.join(dstdir, dir))
                for fname in os.listdir(self.join(srcdir, dir)):
                    if self.check_exclusion(fname):
                        spath = self.join(srcdir, dir, fname)
                        dpath = self.join(dstdir, dir, fname)
                        if os.path.isdir(spath):
                            dirs.append(os.path.join(dir, fname))
                        else:
                            copy_t(spath, dest=dpath)
    def check_exclusion(self, filename):
        from fnmatch import fnmatch
        for excl in self.excludes:
            if fnmatch(filename, excl):
                return False
        else:
            return True

class Mkdir(Task):
    files = ()
    def run(self):
        files = self.get_files(self.get_args('files'), noglob=True)
        for arg in files:
            self.asserttype(arg, str, 'files')
            self.mkdir(self.join(arg))
    @classmethod
    def mkdir(klass, path):
        if os.path.islink(path) or os.path.isfile(path):
            verbose('remove(' + str(path) + ')')
            os.remove(path)
            klass.mkdir(path)
        elif not os.path.isdir(path):
            klass.mkdir(os.path.dirname(path))
            verbose('mkdir(' + str(path) + ')')
            os.mkdir(path)

class Chmod(Task):
    files = ()
    mode = int('666', 8) # gets around Python 2.x vs 3.x octal issue
    def run(self):
        from os import chmod
        mode = self.get_kwarg('mode', int)
        for fname in self.get_files(self.get_args('files')):
            self.asserttype(fname, str, 'files')
            verbose('chmod(' + fname + ', ' + oct(mode) + ')')
            chmod(self.join(fname), mode)

class Tar(Task):
    from os import curdir as root
    name = None
    files = ()
    exclude = ()
    def run(self):
        from tarfile import open
        name = self.get_kwarg('name', str, noNone=True)
        root = self.join(self.get_kwarg('root', str))
        excludes = self.get_kwarg('exclude', (tuple, list))
        if excludes:
            exctest = lambda t, e=excludes: [v for v in e if t.endswith(v)]
            filter = lambda t, e=exctest: not e(t.name) and t or None
            exclusion = lambda t, e=exctest: e(t)
        else:
            exctest = None
            filter = None
            exclusion = None
        toadd = []
        from glob import glob
        queue = list(self.get_files(self.get_args('files'), noglob=True))
        while queue:
            entry = queue[0]
            del queue[0]
            for fn in glob(self.join(root, entry)):
                if exctest and exctest(fn):  # if true, then ignore
                    pass
                elif os.path.islink(fn) or os.path.isfile(fn):
                    toadd.append(fn)
                elif os.path.isdir(fn):
                    fnames = [os.path.join(fn, f) for f in os.listdir(fn)]
                    queue.extend(fnames)
        try:
            file = open(self.join(name), 'w:gz')
        except IOError:
            raise ValueError('no such file or directory: %s' % name)
        else:
            for fname in toadd:
                fn = fname.replace(
                    root + os.sep, ''
                )
                verbose('tar.add(' +
                        str(fname) + ', ' +
                        str(fn) + ')'
                )
                file.add(fname, fn)
            file.close()

class Untar(Task):
    name = None
    root = None
    files = ()
    def run(self):
        from tarfile import open
        name = self.get_kwarg('name', str, noNone=True)
        root = self.get_kwarg('root', str)
        self.asserttype(root, str,'root')
        files = tuple(self.get_args('files'))
        try:
            file = open(self.join(name), 'r:gz')
        except IOError:
            raise ValueError('no such file or directory: %s' % name)
        else:
            fileset = []
            for member in file.getmembers():
                if (member.name.startswith(os.sep) or
                    member.name.startswith(os.pardir)):
                    pass
                elif not files or member.name in files:
                    fileset.append(member)
            for fileinfo in fileset:
                verbose('tar.extract(' + str(fileinfo.name) + ')')
                file.extract(fileinfo, path=(root or ""))
            file.close()

class Zip(Task):
    from os import curdir as root
    name = None
    files = ()
    exclude = ()
    def run(self):
        from zipfile import ZipFile
        name = self.get_kwarg('name', str, noNone=True)
        root = self.join(self.get_kwarg('root', str))
        excludes = tuple(self.get_kwarg('exclude', (tuple, list)))
        if excludes:
            exctest = lambda t, e=excludes: [v for v in e if t.endswith(v)]
            filter = lambda t, e=exctest: not e(t.name) and f or None
            exclusion = lambda t, e=exctest: e(t)
        else:
            exctest = None
            filter = None
            exclusion = None
        toadd = []
        from glob import glob
        queue = list(self.get_files(self.get_args('files'), noglob=True))
        while queue:
            entry = queue[0]
            del queue[0]
            for fn in glob(self.join(root, entry)):
                if exctest and exctest(fn): # if true then ignore
                    pass
                elif os.path.islink(fn) or os.path.isfile(fn):
                    toadd.append(fn)
                elif os.path.isdir(fn):
                    files = [os.path.join(fn, f) for f in os.listdir(fn)]
                    queue.extend(files)
        try:
            file = ZipFile(self.join(name), 'w')
        except IOError:
            raise ValueError('no such file or directory: %s' % name)
        else:
            for fname in toadd:
                fn = fname.replace(
                    root + os.sep, ''
                )
                verbose('zip.add(' + str(fname) + ', ' + str(fn) + ')' )
                file.write(fname, fn)
            file.close()

class Unzip(Task):
    name = None
    root = None
    files = ()
    def run(self):
        from zipfile import ZipFile
        from os import pardir, sep
        from os.path import dirname, join
        name = self.get_kwarg('name', str, noNone=True)
        root = self.get_kwarg('root', str)
        files = tuple(self.get_args('files'))
        try:
            file = ZipFile(self.join(name), 'r')
        except IOError:
            raise ValueError('no such file or directory: %s' % name)
        else:
            fileset = []
            for member in file.namelist():
                if member.startswith(sep) or member.startswith(pardir):
                    pass
                elif not files or member in files:
                    fileset.append(member)
            for member in fileset:
                dname = join(root, member)
                Mkdir.mkdir(dirname(dname))
                verbose('zip.extract(' + str(member) + ')')
                dfile = open(dname, 'wb')
                dfile.write(file.read(member))
            file.close()

class Java(Task):
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
            raise Task.Error("no java program to execute")
        if not os.access(self.java_prog, os.X_OK):
            raise Task.Error("no java program to execute")
    def addprop(self, var, val):
        self.properties.append( (var, val) )
    def run(self):
        from os import environ
        from os.path import pathsep
        jar = self.get_kwarg('jar', str, noNone=True)
        if self.properties:
            if hasformat:
                sp = ['-D{0}={1}'.format(x[0], x[1]) for x in self.properties]
            else:
                sp = ['-D%s=%s' % x for x in self.properties]
        else:
            sp = ()
        cmd = (self.java_prog,) + tuple(sp) + ('-jar', jar,) + \
            tuple([str(s) for s in self.args])
        env = environ.copy()
        if self.classpath:
            env['CLASSPATH'] = pathsep.join(self.classpath)
        Spawn()(
            cmd,
            env=env,
        )

class Unittest(Task):
    modules = ()
    path = ()
    def run(self):
        modules = tuple(self.get_args('modules'))
        import imp, sys, unittest
        try:
            loader = unittest.loader.TestLoader()
        except AttributeError:
            loader = unittest.TestLoader()
        try:
            runner = unittest.runner.TextTestRunner()
        except AttributeError:
            runner = unittest.TextTestRunner()
        try:
            suite = unittest.suite.TestSuite()
        except AttributeError:
            suite = unittest.TestSuite()
        real_sys_name = sys.argv[0]
        try:
            if modules:
                path = [os.path.realpath(p) for p in self.path]
                if not path:
                    path = [os.curdir]
                for modname in modules:
                    sys.argv[0] = modname
                    packet = imp.find_module(modname, path)
                    mod = imp.load_module(modname, *packet)
                    suite.addTests(loader.loadTestsFromModule(mod))
            elif self.path:
                for path in [os.path.realpath(p) for p in self.path]:
                    suite.addTests(loader.discover(path))
            else:
                suite.addTests(loader.discover(os.curdir))
            runner.run(suite)
        finally:
            sys.argv[0] = real_sys_name

