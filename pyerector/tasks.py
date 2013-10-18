#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import logging
import os
import shutil
import sys

from .exception import Error
from .helper import Exclusions, Subcommand
from .config import noTimer
from .base import Task
from .iterators import IdentityMapper, FileMapper, StaticIterator
from .variables import VariableSet

# Python 3.x removed the execfile function
try:
    execfile
except NameError:
    from .py3.execfile import execfile

__all__ = [
    'Chmod', 'Copy', 'CopyTree', 'Echo', 'Egg', 'HashGen', 'Java',
    'Mkdir', 'PyCompile', 'Remove', 'Shebang', 'Spawn', 'SubPyErector',
    'Tar', 'Tokenize', 'Unittest', 'Untar', 'Unzip', 'Zip',
]


class Chmod(Task):
    """Change file permissions.
constructor arguments:
Chmod(*files, mode=0666)"""
    files = ()
    mode = int('666', 8)  # gets around Python 2.x vs 3.x octal issue

    def run(self):
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
            for fn in glob(self.join(root, entry)):
                if excludes.match(fn):  # if true, then ignore
                    pass
                elif os.path.islink(fn) or os.path.isfile(fn):
                    toadd.append(fn)
                elif os.path.isdir(fn):
                    fnames = [os.path.join(fn, f) for f in os.listdir(fn)]
                    queue.extend(fnames)
        #verbose('toadd =', toadd)
        self.manifest(name, root, toadd)
        self.contain(name, root, toadd)
        self.postop(name, root, toadd)

    def preop(self, name, root, excludes):
        pass

    def postop(self, name, root, excludes):
        pass

    def manifest(self, name, root, toadd):
        pass

    def contain(self, name, root, toadd):
        pass


class Copy(Task):
    """Copy files to a destination directory. Exclude standard hidden
files.
constructor arguments:
Copy(*files, dest=<destdir>, exclude=<defaults>)"""
    files = ()
    dest = None
    noglob = False
    #exclude = Exclusions()

    def run(self):
        from .base import Mapper
        dest = self.get_kwarg('dest', str, noNone=False)
        files = self.get_args('files')
        excludes = self.get_kwarg('exclude', (Exclusions, tuple, list))
        if not isinstance(excludes, Exclusions):
            excludes = Exclusions(excludes)
        if len(files) == 1 and dest is None and isinstance(files[0], Mapper):
            fmap = files[0]
        elif len(files) == 1 and dest is not None and not os.path.isdir(dest):
            fmap = IdentityMapper(self.get_files(files), destdir=dest)
        elif dest is not None:
            fmap = FileMapper(self.get_files(files), destdir=dest)
        else:
            raise Error('must supply dest to %s' % self.__class__.__name__)
        self.logger.debug('Copy.fmap = %s', vars(fmap))
        for (sname, dname) in fmap:
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


class Echo(Task):
    """Display a message, arguments are taken as with logger (msg, *args).
This is displayed by the logging module, but at the internal 'DISPLAY'
level created in pyerector.helper."""
    msgs = ()

    def run(self):
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
                h = hashfunc()
                if (os.path.isfile(sname) and
                        not fmap.checkpair(self.join(sname), self.join(dname))):
                    h.update(open(self.join(sname), 'rb').read())
                    self.logger.debug('writing %s', dname)
                    open(self.join(dname), 'wt').write(h.hexdigest() + '\n')


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
        self.properties.append((var, val))

    def run(self):
        from os import environ
        from os.path import pathsep
        jar = self.get_kwarg('jar', str, noNone=True)
        if self.properties:
            sp = ['-D%s=%s' % x for x in self.properties]
        else:
            sp = ()
        cmd = (self.java_prog,) + tuple(sp) + ('-jar', jar,) + \
            tuple([str(s) for s in self.args])
        env = environ.copy()
        if self.classpath:
            env['CLASSPATH'] = pathsep.join(self.classpath)
        rc = Subcommand(cmd)
        if rc.returncode:
            raise Error(self, '%s failed with returncode %d' %
                        (self.__class__.__name__.lower(), rc.returncode)
                        )


class Mkdir(Task):
    """Recursively create directories.
constructor arguments:
Mkdir(*files)"""
    files = ()
    noglob = True

    def run(self):
        files = self.get_files(self.get_args('files'))
        for arg in files:
            self.asserttype(arg, str, 'files')
            self.mkdir(self.join(arg))

    @classmethod
    def mkdir(cls, path):
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
        import py_compile
        fileset = self.get_files(self.get_args('files'))
        if self.version[:1] == sys.version[:1]:  # compile inline
            for s in fileset:
                self.logger.debug('py_compile.compile(%s)', s)
                py_compile.compile(self.join(s))
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
                t, e, tb = sys.exc_info()
                if e.args[0] == 'ENOENT':
                    self.logger.error('%s: Error with %s: %s',
                        self.__class__.__name__, cmd, e.args[1]
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

    def run(self):
        for name in self.get_files(self.get_args('files')):
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
                    w = first.find(' ')
                else:
                    w = first.find(os.linesep)
                first = first.replace(first[len(self.token):w], program)
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
        infile = self.get_kwarg('infile', str)
        outfile = self.get_kwarg('outfile', str)
        errfile = self.get_kwarg('errfile', str)
        infile = infile and self.join(infile) or None
        outfile = outfile and self.join(outfile) or None
        errfile = errfile and self.join(errfile) or None
        env = self.get_kwarg('env', dict)
        cmd = self.get_args('cmd')
        rc = Subcommand(cmd, env=env,
                        stdin=infile, stdout=outfile, stderr=errfile,
                        )
        if rc.returncode < 0:
            raise Error('Subcommand', '%s signal %d raised' % (str(self), abs(rc.returncode)))
        elif rc.returncode > 0:
            raise Error('Subcommand', '%s returned error = %d' % (str(self), rc.returncode))


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
        rc = Subcommand(cmd, wdir=wdir, env=env)
        if rc.returncode < 0:
            raise Error('SubPyErector', '%s signal %d raised' % (str(self), abs(rc.returncode)))
        elif rc.returncode > 0:
            raise Error('SubPyErector', '%s returned error = %d' % (str(self), rc.returncode))


class Tar(Container):
    """Generate a 'tar' archive file.
Constructure arguments:
Tar(*files, name=None, root=os.curdir, exclude=(defaults)."""
    def contain(self, name, root, toadd):
        from tarfile import open
        try:
            tfile = open(self.join(name), 'w:gz')
        except IOError:
            raise ValueError('no such file or directory: %s' % name)
        else:
            for fname in toadd:
                fn = fname.replace(
                    root + os.sep, ''
                )
                self.logger.debug('tar.add(%s, %s)', fname, fn)
                tfile.add(self.join(fname), fn)
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
        pass

    def run(self):
        tokenmap = self.get_kwarg('tokenmap', VariableSet)
        if not isinstance(tokenmap, VariableSet):
            raise TypeError('tokenmap must be a VariableSet instance')
        self.update_tokenmap()
        import re

        def repltoken(m, map=tokenmap):
            self.logger.debug('found %s', m.group(0))
            result = map.get(m.group(0))
            return result is not None and str(result) or ''

        def quote(s):
            return s.replace('\\', r'\\').replace('.', r'\.')\
                    .replace('$', r'\$').replace('(', r'\(')\
                    .replace(')', r'\)').replace('|', r'\|')
        patt = '|'.join(
            [quote(k) for k in self.get_kwarg('tokenmap', VariableSet)]
        )
        tokens = re.compile(r'(%s)' % patt, re.MULTILINE)
        self.logger.debug('patt = %s', str(tokens.pattern))
        mapper = FileMapper(self.get_args('files'),
                            destdir=self.get_kwarg('dest', str),
                            iteratorclass=StaticIterator)
        for (sname, dname) in mapper:
            realcontents = open(self.join(sname), 'rt').read()
            alteredcontents = tokens.sub(repltoken, realcontents)
            if alteredcontents != realcontents:
                open(self.join(dname), 'wt').write(alteredcontents)


class Unittest(Task):
    """Call Python unit tests found.
constructor arguments:
Unittest(*modules, path=())"""
    modules = ()
    path = ()
    script = '''\
import os, sys, imp, unittest
try:
    import coverage
except ImportError:
    pass
else:
    coverage.process_startup()

params = eval(open(sys.argv[1]).read())

verbose = ('verbose' in params and params['verbose']) and 1 or 0
quiet = ('quiet' in params and params['quiet']) and 1 or 0
if quiet:
    verbose = 0

try:
    loader = unittest.loader.TestLoader()
except AttributeError:
    loader = unittest.TestLoader()
if not hasattr(loader, 'discover'):
    class TestLoaderNoDiscover(loader.__class__):
        # ported almost directly from Py2.7 unittest.loader module
        _top_level_dir = None
        def discover(self, start_dir, pattern='test*.py', top_level_dir=None):
            import os, sys
            set_implicit_top = False
            if top_level_dir is None and self._top_level_dir is not None:
                top_level_dir = self._top_level_dir
            elif top_level_dir is None:
                set_implicit_top = True
                top_level_dir = start_dir
            self._top_level_dir = top_level_dir = os.path.abspath(top_level_dir)
            if top_level_dir not in sys.path:
                sys.path.insert(0, top_level_dir)
            is_not_importable = False
            if os.path.isdir(os.path.abspath(start_dir)):
                start_dir = os.path.abspath(start_dir)
                if start_dir != top_level_dir:
                    is_not_importable = \
                        not os.path.isfile(os.path.join(start_dir, '__init__.py'))
            else:  # a module/package name
                try:
                    __import__(start_dir)
                except ImportError:
                    is_not_importable = True
                else:
                    the_module = sys.modules[start_dir]
                    top_part = start_dir.split('.')[0]
                    start_dir = os.path.abspath(os.path.dirname(the_module.__file__))
                    if set_implict_top:
                        module = sys.modules[top_part]
                        full_path = os.path.abspath(module.__file__)
                        if os.path.basename(full_path).lower().__startswith('__init__.py'):
                            self._top_level_dir = os.path.dirname(os.path.dirname(full_path))
                        else:
                            self._top_level_dir = os.path.dirname(full_path)
                        sys.path.remove(top_level_dir)
            if is_not_importable:
                raise ImportError('Start directory is not importable: %s' % start_dir)
            tests = list(self._find_tests(start_dir, pattern))
            return self.suiteClass(tests)
        def _find_tests(self, start_dir, pattern):
            import fnmatch, os
            for path in os.listdir(start_dir):
                full_path = os.path.join(start_dir, path)
                if os.path.isfile(full_path):
                    if not fnmatch.fnmatch(path, '[_a-z]*.py'):
                        # value Python identifiers only
                        continue
                    if not fnmatch.fnmatch(path, pattern):
                        continue
                    try:
                        name = self._get_name_from_path(full_path)
                        module = self._get_module_from_name(name)
                    except:
                        yield self._make_failed_import_test(name, self.suiteClass)
                    else:
                        mod_file = os.path.abspath(getattr(module, '__file__', full_path))
                        realpath = os.path.splitext(mod_file)[0]
                        fullpath_noext = os.path.splitext(full_path)[0]
                        if realpath.lower() != fullpath_noext.lower():
                            module_dir = os.path.dirname(realpath)
                            mod_name = os.path.splitext(os.path.basename(full_path))[0]
                            expected_dir = os.path.dirname(full_path)
                            msg = ('%r module incorrectly imported from %r. Expected %r. '
                                   'Is this moduled globally installed?')
                            raise ImportError(msg % (mod_name, module_dir, expected_dir))
                        yield self.loadTestsFromModule(module)
                elif os.path.isdir(full_path):
                    if not os.path.isfile(os.path.join(full_path, '__init__.py')):
                        continue
                    load_tests = None
                    tests = None
                    if fnmatch.fnmatch(path, pattern):
                        name = self._get_name_from_path(full_path)
                        package = self._get_module_from_name(name)
                        if package is not None:
                            load_tests = getattr(package, 'load_tests', None)
                            tests = self.loadTestsFromModule(package, use_load_tests=False)
                    if load_tests is None:
                        if tests is not None:
                            yield tests
                        for test in self._find_tests(full_path, pattern):
                            yield test
                    else:
                        try:
                            yield load_tests(self, tests, pattern)
                        except Exception:
                            t, e, tb = sys.exc_info()
                            yield self._make_failed_load_tests(package.__name__, e, self.suiteClass)
        def _get_name_from_path(self, path):
            import os, sys
            path = os.path.splitext(os.path.normpath(path))[0]
            _relpath = os.path.relpath(path, self._top_level_dir)
            assert not os.path.isabs(_relpath), 'Path must be within the project'
            assert not _relpath.startswith('..'), 'Path must be within the project'
            name = _relpath.replace(os.path.sep, '.')
            return name
        def _get_module_from_name(self, name):
            import sys
            try:
                __import__(name)
            except ImportError:
                return None
            else:
                return sys.modules[name]
        # return a TestClass subclass wrapped in a suite on error
        def _make_failed_import_test(self, name, suiteClass):
            import traceback
            message = r'Failed to import test module: %s\\n%s' % (name, traceback.format_exc())
            return self._make_failed_test('ModuleImportFailure', name, ImportError(message), suiteClass)
        def _make_failed_load_tests(self, name, exception, suiteClass):
            return self._make_failed_test('LoadTestsFailure', name, exception, suiteClass)
        def _make_failed_test(self, classname, methodname, exception, suiteClass):
            def testFailure(self):
                raise exception
            attrs = {methodname: testFailure}
            TestClass = type(classname, (unittest.TestCase,), attrs)
            return suiteClass((TestClass(methodname),))
    loader = TestLoaderNoDiscover()

try:
    runner = unittest.runner.TextTestRunner(verbosity=verbose)
except AttributeError:
    runner = unittest.TextTestRunner(verbosity=verbose)
try:
    suite = unittest.suite.TestSuite()
except:
    suite = unittest.TestSuite()
real_args = sys.argv[:]
import logging
logging.getLogger('pyerector').setLevel(logging.ERROR)
try:
    if params['modules']:
        path = [os.path.realpath(p) for p in params['path']]
        if not path:
            path = [os.curdir]
        for modname in params['modules']:
            sys.argv[:] = [modname]
            packet = imp.find_module(modname, path)
            mod = imp.load_module(modname, *packet)
            suite.addTests(loader.loadTestsFromModule(mod))
    elif params['path']:
        for path in [os.path.realpath(p) for p in params['path']]:
            suite.addTests(loader.discover(path))
    else:
        suite.addTests(loader.discover(os.curdir))
    runner.run(suite)
finally:
    sys.argv[:] = real_args
'''

    def run(self):
        import tempfile
        pfile = sfile = None
        try:
            # create a parameter file with a serialized set of the arguments
            pfile = tempfile.NamedTemporaryFile(mode='wt',
                                                suffix=".params",
                                                delete=False)
            pfile.write(repr({
                'modules': tuple(self.get_args('modules')),
                'path': self.path,
                'verbose': bool(self.logger.isEnabledFor(logging.INFO)),
                'quiet': bool(self.logger.isEnabledFor(logging.ERROR)),
            }))
            pfile.close()
            sfile = tempfile.NamedTemporaryFile(mode='wt',
                                                suffix=".py",
                                                delete=False)
            sfile.write(self.script)
            sfile.close()
            # call python <scriptname> <paramfile>
            Subcommand((sys.executable, sfile.name, pfile.name), env={'COVERAGE_PROCESS_START': '/dev/null'})
        finally:
            if pfile is not None and os.path.exists(pfile.name):
                os.remove(pfile.name)
            if sfile is not None and os.path.exists(sfile.name):
                os.remove(sfile.name)


class Uncontainer(Task):
    """Super-class for Untar and Unzip."""
    name = None
    root = None
    files = ()

    def run(self):
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
        return None

    def extract_members(self, contfile, fileset, root):
        pass

    @staticmethod
    def retrieve_members(contfile, files):
        return None


class Untar(Uncontainer):
    """Extract a 'tar' archive file.
Untar(*files, name=<tarfilename>, root=None)"""
    def get_file(self, fname):
        import tarfile
        return tarfile.open(self.join(fname), 'r:gz')

    @staticmethod
    def retrieve_members(contfile, files):
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
        for fileinfo in fileset:
            self.logger.debug('tar.extract(%s)', fileinfo.name)
            contfile.extract(fileinfo, path=(root or ""))


class Unzip(Uncontainer):
    """Extract a 'zip' archive file.
Unzip(*files, name=<tarfilename>, root=None)"""
    def get_file(self, fname):
        from zipfile import ZipFile
        return ZipFile(self.join(fname), 'r')

    @staticmethod
    def retrieve_members(contfile, files):
        fileset = []
        files = tuple(files)  # needed for contents test
        for member in contfile.namelist():
            if member.startswith(os.sep) or member.startswith(os.pardir):
                pass
            elif not files or member in files:
                fileset.append(member)
        return fileset

    def extract_members(self, contfile, fileset, root):
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
        from zipfile import ZipFile
        try:
            zfile = ZipFile(self.join(name), 'w')
        except IOError:
            raise ValueError('no such file or directory: %s' % name)
        else:
            for fname in toadd:
                fn = fname.replace(
                    root + os.sep, ''
                )
                self.logger.debug('zip.add(%s, %s)', fname, fn)
                zfile.write(fname, fn)
            zfile.close()


class Egg(Zip):
    """Generate an egg file for Python deployments.
Egg(*files, name=<eggfilename>, root=os.curdir, exclude=(defaults))"""
    def manifest(self, name, root, toadd):
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
        # simulate setup() in a fake distutils and setuptools
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
