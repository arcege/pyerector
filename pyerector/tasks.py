#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import os
import shutil
import sys

from .exception import Error
from .base import Task
from . import debug, verbose, hasformat
from .iterators import FileMapper, MergeMapper, StaticIterator
from .variables import VariableSet


__all__ = [
    'Chmod', 'Copy', 'CopyTree', 'Java', 'Mkdir', 'PyCompile',
    'Remove', 'Shebang', 'Spawn', 'Tar', 'Tokenize', 'Unittest',
    'Untar', 'Unzip', 'Zip',
]

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

class Container(Task):
    """An internal task for subclassing standard classes Tar and Zip."""
    appname = None
    from os import curdir as root
    name = None
    files = ()
    exclude = ()
    def run(self):
        name = self.get_kwarg('name', str, noNone=True)
        root = self.join(self.get_kwarg('root', str))
        excludes = self.get_kwarg('exclude', (tuple, list))
        if excludes:
            exctest = lambda t, e=excludes: [v for v in e if t.endswith(v)]
        else:
            exctest = None
        toadd = []
        from glob import glob
        queue = list(self.get_args('files'))
        while queue:
            entry = queue[0]
            del queue[0]
            for fn in glob(self.join(root, entry)):
                if exctest and exctest(fn): # if true, then ignore
                    pass
                elif os.path.islink(fn) or os.path.isfile(fn):
                    toadd.append(fn)
                elif os.path.isdir(fn):
                    fnames = [os.path.join(fn, f) for f in os.listdir(fn)]
                    queue.extend(fnames)
        self.contain(name, root, toadd)

class Copy(Task):
    files = ()
    dest = None
    noglob = False
    exclude = ('.svn', '.hg', '.git', '*.pyc', '.*.swp')
    def run(self):
        from .base import Mapper
        dest = self.get_kwarg('dest', str, noNone=False)
        files = self.get_args('files')
        if len(files) == 1 and dest is None and isinstance(files[0], Mapper):
            fmap = files[0]
            debug('Copy.fmap =', vars(fmap))
        elif len(files) == 1 and dest is not None and not os.path.isdir(dest):
            fmap = MergeMapper(files[0], destdir=dest)
            debug('Copy.fmap =', vars(fmap))
        elif dest is not None:
            fmap = FileMapper(self.get_files(files),
                              destdir=dest)
            debug('Copy.fmap =', vars(fmap))
        else:
            raise Error('must supply dest to %s' % self.__class__.__name__)
        for (sname, dname) in fmap:
            srcfile = self.join(sname)
            dstfile = self.join(dname)
            if os.path.isfile(dstfile) and fmap.checkpair(srcfile, dstfile):
                debug('uptodate:', dstfile)
            else:
                verbose('copy2(' + str(sname) + ', ' + str(dname) + ')')
                shutil.copy2(srcfile, dstfile)

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

class Mkdir(Task):
    files = ()
    noglob = True
    def run(self):
        files = self.get_files(self.get_args('files'))
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

class PyCompile(Task):
    files = ()
    dest = None
    version = '2'
    def run(self):
        import py_compile
        fileset = self.get_files(self.get_args('files'))
        if self.version[:1] == sys.version[:1]:  # compile inline
            for s in fileset:
                debug('py_compile.compile(%s)' % s)
                py_compile.compile(s)
        else:
            if self.version[:1] == '2':
                cmd = 'python2'
            elif self.version[:1] == '3':
                cmd = 'python3'
            for s in fileset:
                try:
                    Spawn(cmd, '-c', 'from py_compile import compile; compile("%s")' % self.join(s))()
                except:
                    verbose('could not compile', s, 'with', cmd)

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

class Shebang(Copy):
    files = ()
    token = '#!'
    def run(self):
        verbose('starting Shebang')
        program = self.get_kwarg('program', str, noNone=True)
        srcs = self.get_files(self.get_args('files'))
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
                raise Error(str(self), 'returned error = ' + str(rc))
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

class Tar(Container):
    def contain(self, name, root, toadd):
        from tarfile import open
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

class Tokenize(Task):
    """Replace tokens found in tokenmap with their associated values in
each file."""
    files = ()
    dest = None
    tokenmap = VariableSet()
    def update_tokenmap(self):
        pass
    def run(self):
        if not isinstance(self.tokenmap, VariableSet):
            raise TypeError('tokenmap must be a VariableSet instance')
        self.update_tokenmap()
        import re
        def repltoken(m, map=self.tokenmap):
            debug('found', m.group(0))
            result = map.get(m.group(0))
            return result is not None and result.value or ''
        def quote(s):
            return s.replace('\\', r'\\').replace('.', r'\.')\
                    .replace('$', r'\$').replace('(', r'\(')\
                    .replace(')', r'\)').replace('|', r'\|')
        patt = '|'.join(
            [quote(k) for k in self.get_kwarg('tokenmap', VariableSet)]
        )
        tokens = re.compile(r'(%s)' % patt, re.MULTILINE)
        debug('patt =', str(tokens.pattern))
        mapper = FileMapper(self.get_args('files'),
                            destdir=self.get_kwarg('dest', str),
                            iteratorclass=StaticIterator)
        for (sname, dname) in mapper:
            realcontents = open(self.join(sname), 'rt').read()
            m = tokens.search(realcontents)
            alteredcontents = tokens.sub(repltoken, realcontents)
            if alteredcontents != realcontents:
                open(self.join(dname), 'wt').write(alteredcontents)

class Unittest(Task):
    modules = ()
    path = ()
    script = '''\
import os, sys, imp, unittest

params = eval(open(sys.argv[1]).read())

verbose = ('verbose' in params and params['verbose']) and 1 or 0

try:
    loader = unittest.loader.TestLoader()
except AttributeError:
    loader = unittest.TestLoader()
if True: #not hasattr(loader, 'discover'):
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
                        except Exception, e:
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
            __import__(name)
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
        import imp, tempfile, unittest
        pfile = sfile = None
        try:
            # create a parameter file with a serialized set of the arguments
            pfile = tempfile.NamedTemporaryFile(mode='wt',
                                                suffix=".params",
                                                delete=False)
            pfile.write(repr({
                'modules': tuple(self.get_args('modules')),
                'path': self.path,
                'verbose': bool(verbose),
            }))
            pfile.close()
            sfile = tempfile.NamedTemporaryFile(mode='wt',
                                                suffix=".py",
                                                delete=False)
            sfile.write(self.script)
            sfile.close()
            # call python <scriptname> <paramfile>
            Spawn(sys.executable, sfile.name, pfile.name)()
        finally:
            if pfile is not None and os.path.exists(pfile.name):
                os.remove(pfile.name)
            if sfile is not None and os.path.exists(sfile.name):
                os.remove(sfile.name)

class Uncontainer(Task):
    name = None
    root = None
    files = ()
    def run(self):
        name = self.get_kwarg('name', str, noNone=True)
        root = self.get_kwarg('root', str)
        self.asserttype(root, str, 'root')
        files = tuple(self.get_args('files'))
        try:
            contfile = self.get_file(name)
        except IOError:
            raise ValueError('no such file or directory: %s' % name)
        else:
            fileset = self.retrieve_members(contfile, files)
            self.extract_members(contfile, fileset, root)
            contfile.close()

class Untar(Uncontainer):
    def get_file(self, fname):
        from tarfile import open
        return open(self.join(fname), 'r:gz')
    def retrieve_members(self, contfile, files):
        fileset = []
        for member in contfile.getmembers():
            if (member.name.startswith(os.sep) or
                member.name.startswith(os.pardir)):
                pass
            elif not files or member.name in files:
                fileset.append(member)
        return fileset
    def extract_members(self, contfile, fileset, root):
        for fileinfo in fileset:
            verbose('tar.extract(' + str(fileinfo.name) + ')')
            contfile.extract(fileinfo, path=(root or ""))

class Unzip(Uncontainer):
    def get_file(self, fname):
        from zipfile import ZipFile
        return ZipFile(self.join(fname), 'r')
    def retrieve_members(self, contfile, files):
        fileset = []
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
            verbose('zip.extract(' + str(member) + ')')
            dfile = open(dname, 'wb')
            dfile.write(contfile.read(member))

class Zip(Container):
    def contain(self, name, root, toadd):
        from zipfile import ZipFile
        try:
            file = ZipFile(self.join(name), 'w')
        except IOError:
            raise ValueError('no such file or directory: %s' % name)
        else:
            for fname in toadd:
                fn = fname.replace(
                    root + os.sep, ''
                )
                verbose('zip.add(' + str(fname) + ',' + str(fn) + ')' )
                file.write(fname, fn)
            file.close()

