#!/usr/bin/python
# Copyright @ 2010-2012 Michael P. Reilly. All rights reserved.
# pyerector.py
#
# Options available to PyErector():
#    -h|--help               display arguments and options
#    -v|--verbose            display debugging output
#    -N|--dry-run            do not perform actual steps (bypass 'run()' method)
#    -d=DIR|--directory=DIR  change the basedir value
# Options available to pyerector.py:
#    help                    call the 'help' target and exit
#    version                 display library version
#    test                    run test of pyerector.py
#
# Example code:
# ---------------------------------------------
# from pyerector import *
# Compile.dependencies = ('PythonPrecompile',)
# class PreCompile_utd(Uptodate):
#     sources = ('*.py',)
#     destinations = ('build/*.pyc',)
# class PyCopy_t(Copy):
#     sources = ('*.py',)
#     destination = 'build'
# class PyCopy(Target):
#     files = ('*.py',)
#     tasks = ("PyCopy_t",)
# class PythonPreCompile(Target):
#     dependencies = ("PyCopy",)
#     uptodates = ("PreCompile_utd",)
#     files = ('build/*.py',)
#     def run(self):
#         from py_compile import compile
#         for file in self.get_files():
#             compile(file)
#
# PyErector()
# ---------------------------------------------
# $Id: pyerector.py 907 2012-11-05 21:29:03Z reillym $

from __future__ import print_function
_RCS_VERSION = '$Revision: 30 $'

from sys import version
if version < '3':
    def u(x):
        from codecs import unicode_escape_decode
        return unicode_escape_decode(x)[0]
else:
    def u(x):
        return x

# Future Py3000 work prevents the use of string formatting using '%'
# trying to use both string formatting and ''.format is UGLY!!!!
# A LOT of the code below will be using the less efficient string
# concatentation which is supported across both sets of releases.
try:
    ''.format
except AttributeError:
    hasformat = False
else:
    hasformat = True

__all__ = [
  'Target', 'Uptodate', 'pymain', 'PyErector', 'symbols_to_global',
  'DirList', 'FileList',
  # standard targets
  'All', 'Default', 'Help', 'Clean', 'Init', 'InitDirs',
  'Build', 'Compile', 'Dist', 'Packaging', 'Test',
  # tasks
  'Task', 'Spawn', 'Remove', 'Copy', 'CopyTree', 'Mkdir', 'Chmod', 'Java',
  'Shebang', 'Tar', 'Unittest', 'Untar', 'Unzip', 'Zip',
]

# helper routines
def normjoin(*args):
    from os.path import join, normpath
    return normpath(join(*args))

class Config:
    initialized = False
    _basedir = None
    def __init__(self, basedir=None):
        from os import curdir
        if basedir is not None:
            self.basedir = basedir
    def _get_basedir(self):
        return self._basedir
    def _set_basedir(self, value):
        from os.path import realpath, isdir
        dir = realpath(value)
        if isdir(dir):
            self._basedir = dir
        else:
            raise ValueError('no such file or directory: %s' % dir)
    basedir = property(_get_basedir, _set_basedir)

class Verbose(object):
    from os import linesep as eoln
    from sys import stdout as stream
    prefix = ''
    def __init__(self, state=False):
        from os import environ
        self.state = bool(state)
        if 'PYERECTOR_PREFIX' in environ:
            self.prefix = environ['PYERECTOR_PREFIX'].decode('UTF-8')
    def __bool__(self):
        return self.state
    __nonzero__ = __bool__
    def on(self):
        self.state = True
    def off(self):
        self.state = False
    def _write(self, msg):
        if self.state:
            if self.prefix != '':
                self.stream.write(u(self.prefix))
                self.stream.write(u(': '))
            self.stream.write(u(msg))
            self.stream.write(u(self.eoln))
            self.stream.flush()
    def __call__(self, *args):
        self._write(u(' ').join([u(str(s)) for s in args]))
verbose = Verbose()
noop = Verbose()
from os import environ
debug = Verbose('DEBUG' in environ and environ['DEBUG'] != '')
del environ

# the main program, an instance to be called by pyerect program
class PyErector(object):
    try:
        import argparse
        parser = argparse.ArgumentParser(description='Pyerector build system')
        del argparse
        parser.add_argument('targets', metavar='TARGET', nargs='*',
                            help='name of target to call, default is "default"')
        parser.add_argument('--directory', '-d',
                            help='base directory')
        parser.add_argument('--dry-run', '-N', dest='noop', action='store_true',
                            help='do not perform operations')
        parser.add_argument('--verbose', '-v', action='store_true',
                            help='more verbose output')
    except ImportError:
        import optparse
        parser = optparse.OptionParser(description='Pyerector build system')
        parser.add_option('--directory', '-d', help='base directory')
        parser.add_option('--dry-run', '-N', dest='noop', action='store_true',
                          help='do not perform operations')
        parser.add_option('--verbose', '-v', action='store_true',
                          help='more verbose output')
    def __init__(self, *args):
        from sys import argv
        self.basedir = None
        self.targets = []
        self.arguments(args or argv[1:])
        self.validate_targets()
        self.run()
    def arguments(self, args):
        global verbose, noop
        import __main__
        args = self.parser.parse_args(args)
        if isinstance(args, tuple):
            args, arglist = args
            args.targets = arglist
        if args.verbose:
            verbose.on()
        if args.noop:
            noop.on()
        if args.directory:
            self.basedir = args.directory
        if args.targets:
            self.targets = []
            all_targets = Target.get_targets()
            for name in args.targets:
                try:
                    obj = all_targets[name.capitalize()]
                except KeyError:
                    raise SystemExit('Error: unknown target: ' + str(name))
                else:
                    if not issubclass(obj, Target):
                        raise SystemExit('Error: unknown target: ' + str(name))
                    self.targets.append(obj)
        else:
            self.targets = [__main__.Default]
    def handle_error(self, text=''):
        from sys import argv, exc_info
        if debug:
            raise
        else:
            e = exc_info()[1]
            if text:
                raise SystemExit('%s: %s' % (text, e))
            else:
                raise SystemExit(str(e))
    def validate_targets(self):
        # validate the dependency tree, make sure that all are subclasses of
        # Target, validate all Uptodate values and all Task values
        for target in self.targets:
            try:
                target.validate_tree()
            except ValueError:
                self.handle_error('Error')
    def run(self):
        # run all targets in the tree of each argument
        for target in self.targets:
            try:
                target(basedir=self.basedir)()
            except ValueError:
                self.handle_error()
            except KeyboardInterrupt:
                self.handle_error()
            except AssertionError:
                self.handle_error('AssertionError')
pymain = PyErector

# helper function to reference classes in current scope
def symbols_to_global(*classes, **kwargs):
    from sys import modules
    if 'modname' in kwargs:
        modname = kwargs['modname']
    else:
        modname = __name__
    moddict = modules[modname].__dict__
    for klass in classes:
        moddict[klass.__name__] = klass

# the classes

# a helper class to handle file/directory lists better
class FileIterator(object):
    def __init__(self, path, exclude=None, basedir=None):
        from os import curdir
        super(FileIterator, self).__init__()
        if isinstance(path, (tuple, list)):
            self.pool = list(path)
        else:
            self.pool = [path]
        self.pos = 0
        self.exclude = exclude
        if basedir is None:
            basedir = _Initer.config.basedir or curdir
        self.basedir = basedir
    def __iter__(self):
        self.pos = 0
        return self
    def next(self):
        while True:
            if self.pos >= len(self.pool):
                raise StopIteration
            item = self.pool[self.pos]
            self.pos += 1
            if not self.apply_exclusion(item):
                return item
    def apply_exclusion(self, filename):
        from fnmatch import fnmatch
        result = self.exclude and fnmatch(filename, self.exclude)
        debug('apply_exclusion(%s, %s) =' % (filename, self.exclude),
                result)
        return result
class FileList(FileIterator):
    def __init__(self, *args, **kwargs):
        super(FileList, self).__init__(path=args, **kwargs)

class DirList(FileIterator):
    def __init__(self, path, recurse=False, filesonly=True, **kwargs):
        super(DirList, self).__init__(path, **kwargs)
        self.recurse = bool(recurse)
        self.filesonly = bool(filesonly)
        self.update_dirpath()
    def update_dirpath(self):
        from os import listdir
        from os.path import basename, isdir, isfile, islink, join
        dirs = self.pool[:]
        paths = []
        while dirs:
            thisdir = dirs[0]
            del dirs[0]
            if not self.filesonly:
                paths.append(thisdir)
            if not self.apply_exclusion(basename(thisdir)):
                for name in listdir(join(self.basedir, thisdir)):
                    spath = join(thisdir, name)
                    dpath = join(self.basedir, thisdir, name)
                    if self.apply_exclusion(name):
                        pass
                    elif islink(dpath) or isfile(dpath):
                        paths.append(spath)
                    elif self.recurse:
                        dirs.append(spath)
        self.pool[:] = paths # replace the pool with the gathered set

# the base class to set up the others
class _Initer(object):
    class Error(Exception):
        def __str__(self):
            return str(self[0]) + ': ' + str(self[1])
        def __format__(self, format_spec):
            if isinstance(self, unicode):
                return unicode(str(self))
            else:
                return str(self)
    config = Config()
    from os import curdir
    def __init__(self, basedir=None, curdir=curdir):
        from os.path import realpath
        if basedir is None:
            basedir = curdir
        if not self.config.initialized:
            self.config.basedir = realpath(basedir)
            self.config.initialized = True
    del curdir
    def get_files(self, files=None, noglob=False, subdir=None):
        from glob import glob
        from os import curdir
        if noglob:
            glob = lambda x: [x]
        if subdir is None:
            subdir = curdir
        if not files:
            files = self.files
        filelist = []
        for entry in files:
            if isinstance(entry, FileIterator):
                s = [self.join(e) for e in entry]
            else:
                s = glob(self.join(subdir, entry))
            filelist.extend(s)
        return filelist
    def join(self, *path):
        return normjoin(self.config.basedir, *path)
    def asserttype(self, value, typeval, valname):
        if isinstance(typeval, type):
            typename = typeval.__name__
        else:
            typename = ' or '.join(t.__name__ for t in typeval)
        text = "Must supply %s to '%s' in '%s'" % (
            typename, valname, self.__class__.__name__
        )
        assert isinstance(value, typeval), text
    def get_kwarg(self, name, typeval, noNone=False):
        if name in self.kwargs:
            value = self.kwargs[name]
        else:
            value = getattr(self, name)
        if noNone or value is not None:
            self.asserttype(value, typeval, name)
        elif noNone and value is None:
            raise ValueError("no '%s' for '%s'" %
                                (name, self.__class__.__name__))
        return value
    def get_args(self, name):
        if self.args:
            value = self.args
        else:
            value = getattr(self, name)
        self.asserttype(value, (tuple, list), name)
        return value

class Uptodate(_Initer):
    sources = ()
    destinations = ()
    def __call__(self, *args):
        klsname = self.__class__.__name__
        if not self.sources or not self.destinations:
            verbose(klsname, '*>', False)
            return False
        srcs = self.get_files(self.sources)
        dsts = self.get_files(self.destinations)
        # if no actual destination files then nothing is uptodate
        if not dsts and self.destinations:
            verbose(klsname, '+>', False)
            return False
        result = self.check(srcs, dsts)
        verbose(klsname, '=>', result and 'False' or 'True')
        return result
    def check(srcs, dsts):
        # compare the latest mtime of the sources with the earliest
        # mtime of the destinations
        from os.path import getmtime
        try:
            from sys import maxsize as maxint
        except ImportError:
            from sys import maxint
        latest_src = reduce(max, [getmtime(s) for s in srcs], 0)
        earliest_dst = reduce(min, [getmtime(d) for d in dsts], maxint)
        result = round(earliest_dst, 4) >= round(latest_src, 4)
        return result
    check = staticmethod(check)
    def checkpair(src, dst):
        # compare the mtime of the source with the mtime of the
        # destination
        from os.path import getmtime
        return round(getmtime(dst), 4) >= round(getmtime(src), 4)
    checkpair = staticmethod(checkpair)

class Target(_Initer):
    from sys import stdout as stream
    dependencies = ()
    uptodates = ()
    tasks = ()
    # if True, then 'been_called' always returns False, allowing for
    # reexecution
    allow_reexec = False
    # if True, then 'been_called' returns True, preventing
    # reexecution
    _been_called = False
    def get_been_called(self):
        return not self.allow_reexec and self.__class__._been_called
    def set_been_called(self, value):
        self.__class__._been_called = value
    been_called = property(get_been_called, set_been_called)
    def __str__(self):
        return self.__class__.__name__
    @classmethod
    def validate_tree(klass):
        name = klass.__name__
        targets = klass.get_targets()
        uptodates = klass.get_uptodates()
        tasks = klass.get_tasks()
        try:
            deps = klass.dependencies
        except AttributeError:
            pass
        else:
            for dep in deps:
                if dep not in targets:
                    raise ValueError(
                        str(name) + ': invalid dependency: ' + str(dep)
                    )
                targets[dep].validate_tree()
        try:
            utds = klass.uptodates
        except AttributeError:
            pass
        else:
            for utd in utds:
                if utd not in uptodates:
                    raise ValueError(
                        str(name) + ': invalid uptodate: ' + str(utd)
                    )
        try:
            tsks = klass.tasks
        except AttributeError:
            pass
        else:
            for tsk in tsks:
                if tsk not in tasks:
                    raise ValueError(
                        str(name) + ': invalid task: ' + str(tsk)
                    )
    def call_uptodate(self, klassname):
        uptodates = self.get_uptodates()
        try:
            klass = uptodates[klassname]
        except KeyError:
            if not debug:
                raise self.Error(str(self), 'no such uptodate: ' + str(klassname))
            else:
                raise
        return klass(basedir=self.config.basedir)()
    def call_dependency(self, klassname):
        targets = self.get_targets()
        try:
            klass = targets[klassname]
        except KeyError:
            if not debug:
                raise self.Error(str(self), 'no such dependency: ' + str(klassname))
            else:
                raise
        klass(basedir=self.config.basedir)()
    def call_task(self, klassname, args):
        tasks = self.get_tasks()
        try:
            klass = tasks[klassname]
        except KeyError:
            if not debug:
                raise self.Error(str(self), 'no such task: ' + str(klassname))
            else:
                raise
        return klass(basedir=self.config.basedir)(*args)
    def __call__(self, *args):
        from sys import exc_info
        if self.been_called:
            return
        if self.uptodates:
            for utd in self.uptodates:
                if not self.call_uptodate(utd):
                    break
            else:
                self.verbose('uptodate.')
                return
        for dep in self.dependencies:
            self.call_dependency(dep)
        for task in self.tasks:
            try:
                self.call_task(task, args) # usually args would be (), but...
            except self.Error:
                if not debug:
                    e = exc_info()
                    raise self.Error(str(self) + ':' + str(e[1][0]), e[1][1]), None, e[2]
                else:
                    raise
        try:
            self.run()
        except (TypeError, RuntimeError, AttributeError):
            raise
        except Task.Error:
            if not debug:
                e = exc_info()
                raise self.Error(str(self) + ':' + str(e[1][0]), e[1][1]), None, e[2]
            else:
                raise
        except self.Error:
            raise
        except Exception:
            if not debug:
                e = exc_info()
                raise self.Error(str(self), e[1]), None, e[2]
            else:
                raise
        else:
            self.verbose('done.')
            self.been_called = True
    def run(self):
        pass
    def verbose(self, *args):
        if verbose.prefix != '':
            self.stream.write(u(verbose.prefix))
            self.stream.write(u(': '))
        self.stream.write(u(str(self)))
        self.stream.write(u(': '))
        self.stream.write(u(' ').join([u(str(s)) for s in args]))
        self.stream.write(u('\n'))
        self.stream.flush()
    @staticmethod
    def get_tasks():
        import __main__
        if not hasattr(__main__, '_tasks_cache'):
            tasks = {}
            for name, obj in list(vars(__main__).items()):
                if not name.startswith('_') \
                   and obj is not Task \
                   and isinstance(obj, type(Task)) \
                   and issubclass(obj, Task):
                    tasks[name] = obj
            setattr(__main__, '_tasks_cache', tasks)
        return getattr(__main__, '_tasks_cache')
    @staticmethod
    def get_targets():
        import __main__
        if not hasattr(__main__, '_targets_cache'):
            targets = {}
            for name, obj in list(vars(__main__).items()):
                if not name.startswith('_') \
                   and obj is not Target \
                   and isinstance(obj, type(Target)) \
                   and issubclass(obj, Target):
                    targets[name] = obj
            setattr(__main__, '_targets_cache', targets)
        return getattr(__main__, '_targets_cache')
    @staticmethod
    def get_uptodates():
        import __main__
        if not hasattr(__main__, '_uptodates_cache'):
            uptodates = {}
            for name, obj in list(vars(__main__).items()):
                if not name.startswith('_') \
                   and obj is not Uptodate \
                   and isinstance(obj, type(Uptodate)) \
                   and issubclass(obj, Uptodate):
                    uptodates[name] = obj
            setattr(__main__, '_uptodates_cache', uptodates)
        return getattr(__main__, '_uptodates_cache')

# Tasks
class Task(_Initer):
    args = []
    def __str__(self):
        return self.__class__.__name__
    def __call__(self, *args, **kwargs):
        from sys import exc_info
        self.handle_args(args, kwargs)
        if noop:
            noop('Calling %s(*%s, **%s)' % (self, args, kwargs))
            return
        try:
            rc = self.run()
        except (TypeError, RuntimeError):
            raise
        except Exception:
            if not debug:
                e = exc_info()
                raise self.Error(str(self), e[1]), None, e[2]
            else:
                raise
        if rc:
            raise self.Error(str(self), 'return error = ' + str(rc))
    def run(self):
        pass
    def handle_args(self, args, kwargs):
        self.args = list(args)
        self.kwargs = dict(kwargs)

# standard tasks

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
        from os import environ
        cmd = self.get_args('cmd')
        from os import WIFSIGNALED, WTERMSIG, WEXITSTATUS
        try:
            from subprocess import call
            realenv = environ.copy()
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
                raise self.Error(str(self), 'signal ' + str(abs(rc)) + 'raised')
            elif rc > 0:
                raise self.Error(str(self), 'returned error + ' + str(rc))
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
                if ename in environ:
                    oldenv[ename] = environ[ename]
                else:
                    oldenv[ename] = None
                environ[ename] = env[ename]
            rc = Popen3(pcmd, capturestderr=False, bufsize=0).wait()
            if WIFSIGNALED(rc):
                raise self.Error(str(self),
                                 'signal ' + str(WTERMSIG(rc)) + 'raised')
            elif WEXITSTATUS(rc):
                raise self.Error(str(self), 'returned error = ' + str(rc))
            for ename in env:
                if oldenv[ename] is None:
                    del environ[ename]
                else:
                    environ[ename] = oldenv[ename]
class Remove(Task):
    files = ()
    noglob = False
    def run(self):
        from os import remove
        from os.path import isdir, isfile, islink
        from shutil import rmtree
        files = tuple(self.get_args('files'))
        for fname in self.get_files(files, self.noglob):
            self.asserttype(fname, str, 'files')
            if isfile(fname) or islink(fname):
                verbose('remove(' + str(fname) + ')')
                remove(fname)
            elif isdir(fname):
                verbose('rmtree(' + str(fname) + ')')
                rmtree(fname)
class Copy(Task):
    files = ()
    dest = None
    noglob = False
    def wantnoglob(self):
        return (('noglob' in self.kwargs and self.kwargs['noglob']) or
                self.noglob)
    def run(self):
        from os.path import basename, isdir, isfile, join
        from shutil import copy2
        verbose('starting Copy')
        dst = self.join(self.get_kwarg('dest', str, noNone=True))
        srcs = self.get_files(self.get_args('files'), noglob=self.wantnoglob())
        dstisdir = isdir(dst)
        for fname in srcs:
            self.asserttype(fname, str, 'files')
            if dstisdir:
                dstfile = join(dst, basename(fname))
            else:
                dstfile = dst
            if isfile(dstfile) and Uptodate.checkpair(fname, dstfile):
                debug('uptodate:', dstfile)
            else:
                verbose('copy2(' + str(fname) + ', ' + str(dstfile) + ')')
                copy2(fname, dstfile)
class Shebang(Copy):
    files = ()
    token = '#!'
    def run(self):
        from shutil import copyfileobj
        verbose('starting Shebang')
        program = self.get_kwarg('program', str, noNone=True)
        srcs = self.get_files(self.get_args('files'), noglob=self.wantnoglob())
        try:
            from io import BytesIO as StringIO
        except ImportError:
            from StringIO import StringIO
        from os import linesep
        for fname in srcs:
            inf = open(fname, 'r')
            outf = StringIO()
            first = inf.readline()
            if first.startswith(self.token):
                if ' ' in first:
                    w = first.find(' ')
                else:
                    w = first.find(linesep)
                first = first.replace(first[len(self.token):w], program)
                outf.write(first)
            else:
                outf.write(first)
            copyfileobj(inf, outf)
            inf.close()
            outf.seek(0)
            inf = open(fname, 'w')
            copyfileobj(outf, inf)
class CopyTree(Task):
    srcdir = None
    dstdir = None
    excludes = ('.svn',)
    def run(self):
        from fnmatch import fnmatch
        from os import curdir, error, listdir
        from os.path import exists, join, isdir
        srcdir = self.get_kwarg('srcdir', str, noNone=True)
        dstdir = self.get_kwarg('dstdir', str, noNone=True)
        if not exists(self.join(srcdir)):
            raise error(2, "No such file or directory: " + srcdir)
        elif not isdir(self.join(srcdir)):
            raise error(20, "Not a directory: " + srcdir)
        copy_t = Copy()
        mkdir_t = Mkdir()
        # override what is set in the class definition
        copy_t.noglob = True
        dirs = [curdir]
        while dirs:
            dir = dirs[0]
            del dirs[0]
            if self.check_exclusion(dir):
                mkdir_t(self.join(dstdir, dir))
                for fname in listdir(self.join(srcdir, dir)):
                    if self.check_exclusion(fname):
                        spath = self.join(srcdir, dir, fname)
                        dpath = self.join(dstdir, dir, fname)
                        if isdir(spath):
                            dirs.append(join(dir, fname))
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
        for arg in self.get_args('files'):
            self.asserttype(arg, str, 'files')
            self.mkdir(self.join(arg))
    @classmethod
    def mkdir(klass, path):
        from os import mkdir, remove
        from os.path import dirname, isdir, isfile, islink
        if islink(path) or isfile(path):
            verbose('remove(' + str(path) + ')')
            remove(path)
            klass.mkdir(path)
        elif not isdir(path):
            klass.mkdir(dirname(path))
            verbose('mkdir(' + str(path) + ')')
            mkdir(path)
class Chmod(Task):
    files = ()
    mode = int('666', 8) # gets around Python 2.x vs 3.x octal issue
    def run(self):
        from os import chmod
        mode = self.get_kwarg('mode', int)
        for fname in self.get_files(self.get_args('files')):
            self.asserttype(fname, str, 'files')
            verbose('chmod(' + fname + ', ' + oct(mode) + ')')
            chmod(fname, mode)
class Tar(Task):
    from os import curdir as root
    name = None
    files = ()
    exclude = ()
    def run(self):
        from tarfile import open
        from os import sep, listdir
        from os.path import join, islink, isfile, isdir
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
        # do not use Task.get_files()
        from glob import glob
        queue = list(self.get_args('files'))
        while queue:
            entry = queue[0]
            del queue[0]
            for fn in glob(self.join(root, entry)):
                if exctest and exctest(fn):  # if true, then ignore
                    pass
                elif islink(fn) or isfile(fn):
                    toadd.append(fn)
                elif isdir(fn):
                    fnames = [join(fn, f) for f in listdir(fn)]
                    queue.extend(fnames)
        file = open(self.join(name), 'w:gz')
        for fname in toadd:
            fn = fname.replace(
                root + sep, ''
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
        from os import pardir, sep
        from os.path import join
        name = self.get_kwarg('name', str, noNone=True)
        root = self.get_kwarg('root', str)
        self.asserttype(root, str,'root')
        files = tuple(self.get_args('files'))
        file = open(name, 'r:gz')
        fileset = []
        for member in file.getmembers():
            if member.name.startswith(sep) or member.name.startswith(pardir):
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
        from os import listdir, sep
        from os.path import isdir, isfile, islink, join
        name = self.get_kwarg('name', str, noNone=True)
        root = self.join(self.get_kwarg('root', str))
        excludes = tuple(self.get_kwarg('exclude', (tuple, list)))
        files = tuple(self.get_args('files'))
        if excludes:
            exctest = lambda t, e=excludes: [v for v in e if t.endswith(v)]
            filter = lambda t, e=exctest: not e(t.name) and f or None
            exclusion = lambda t, e=exctest: e(t)
        else:
            exctest = None
            filter = None
            exclusion = None
        toadd = []
        # do not use Task.get_files()
        from glob import glob
        queue = list(files)
        while queue:
            entry = queue[0]
            del queue[0]
            for fn in glob(self.join(root, entry)):
                if exctest and exctest(fn): # if true then ignore
                    pass
                elif islink(fn) or isfile(fn):
                    toadd.append(fn)
                elif isdir(fn):
                    files = [join(fn, f) for f in listdir(fn)]
                    queue.extend(files)
        file = ZipFile(self.join(name), 'w')
        for fname in toadd:
            fn = fname.replace(
                root + sep, ''
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
        file = ZipFile(name, 'r')
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
    java_home = environ['JAVA_HOME']
    classpath = ()
    properties = []
    del environ
    jar = None
    def __init__(self):
        Task.__init__(self)
        from os import access, X_OK
        from os.path import expanduser, exists, join
        import os
        if exists(self.java_home):
            self.java_prog = join(self.java_home, 'bin', 'java')
        elif exists(expanduser(join('~', 'java'))):
            self.java_prog = expanduser(
                join('~', 'java', 'bin', 'java')
            )
        else:
            raise Task.Error("no java program to execute")
        if not access(self.java_prog, X_OK):
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
        import imp, unittest
        from sys import argv
        from os import curdir
        from os.path import realpath
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
        real_sys_name = argv[0]
        try:
            if modules:
                path = [realpath(p) for p in self.path]
                if not path:
                    path = [curdir]
                for modname in modules:
                    argv[0] = modname
                    packet = imp.find_module(modname, path)
                    mod = imp.load_module(modname, *packet)
                    suite.addTests(loader.loadTestsFromModule(mod))
            elif self.path:
                for path in [realpath(p) for p in self.path]:
                    suite.addTests(loader.discover(path))
            else:
                suite.addTests(loader.discover(curdir))
            runner.run(suite)
        finally:
            argv[0] = real_sys_name

# standard targets

class Help(Target):
    """This information"""
    def run(self):
        for name, obj in sorted(self.get_targets().items()):
            if hasformat:
                print('{0:20}  {1}'.format(
                        obj.__name__.lower(),
                        obj.__doc__ or ""
                    )
                )
            else:
                print('%-20s  %s' % (obj.__name__.lower(), obj.__doc__ or ""))
class Clean(Target):
    """Clean directories and files used by the build"""
    files = ()
    def run(self):
        Remove(basedir=self.config.basedir)(*self.files)
class InitDirs(Target):
    """Create initial directories"""
    files = ()
    def run(self):
        Mkdir(basedir=self.config.basedir)(*self.files)
class Init(Target):
    """Initialize the build."""
    dependencies = ("InitDirs",)
class Compile(Target):
    """Do something interesting."""
    # meant to be overriden
class Build(Target):
    """The primary build."""
    dependencies = ("Init", "Compile")
class Packaging(Target):
    """Do something interesting."""
    # meant to be overriden
class Dist(Target):
    """The primary packaging."""
    dependencies = ("Build", "Packaging")
    # may be overriden
class Test(Target):
    """Run (unit)tests."""
    dependencies = ("Build",)
    tasks = ("Unittest",)
# default target
class All(Target):
    """Do it all"""
    dependencies = ("Clean", "Dist", "Test")
class Default(Target):
    dependencies = ("Dist",)

def get_version():
    return _RCS_VERSION.replace('Revision: ', '').replace('$', '')

assert _Initer.config is Target.config, "Not the same Config instance"

if __name__ == '__main__':
    from os.path import splitext, basename
    from sys import argv
    progname = splitext(basename(argv[0]))[0]
    if len(argv) == 1 or argv[1] == 'help':
        print(progname, 'help|version|test|unit')
    elif argv[1] == 'version':
        print(progname, get_version())
    elif argv[1] == 'test':
        test()
    elif argv[1] == 'unit':
        argv[1:] = []
        unittest.main()
    else:
        print('Error: %s: Invalid argument: %s' % (progname, argv[1]))
