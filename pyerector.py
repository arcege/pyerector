#!/usr/bin/python
# pymakelib.py
#
# from pymakelib import *
# Compile.dependencies = ('PythonPrecompile',)
# class PreCompile_utd(Uptodate):
#     sources = ('*.py',)
#     destinations = ('build/*.pyc',)
# class PyCopy(Target):
#     files = ('*.py',)
#     def run(self):
#         from glob import glob
#         for entry in self.files:
#             for file in glob(join(self.basedir, entry)):
#                 self.copy(file, 'build')
# class PythonPreCompile(Target):
#     dependencies = ("PyCopy",)
#     uptodates = ("PreCompile_utd",)
#     files = ('build/*.py',)
#     def run(self):
#         from os.path import join
#         from py_compile import compile
#         from glob import glob
#         for entry in self.files:
#             for file import glob(join(self.basedir, entry)):
#                 compile(file)
#
# $Id$

__all__ = [
  'Target', 'Uptodate', 'pymain',
  # standard targets
  'All', 'Default', 'Help', 'Clean', 'Init', 'InitDirs',
  'Build', 'Compile', 'Dist',
]

class _Initer:
    from os import curdir
    def __init__(self, basedir=curdir):
        from os.path import normpath, realpath
        self.basedir = normpath(realpath(basedir))
    del curdir

class Uptodate(_Initer):
    sources = ()
    destinations = ()
    def __call__(self, *args):
        from glob import glob
        from os.path import getmtime, join
        from sys import maxint
        self.srcs = []
        self.dsts = []
        if not self.sources or not self.destinations:
            return False
        for filepatt in self.sources:
            self.srcs.extend(glob(join(self.basedir, filepatt)))
        for filepatt in self.destinations:
            self.dsts.extend(glob(join(self.basedir, filepatt)))
        # if no actual destination files then nothing is uptodate
        if not self.dsts and self.destinations:
            return False
        # compare the latest mtime of the sources with the earliest
        # mtime of the destinations
        latest_src = 0
        earliest_dst = maxint
        for src in self.srcs:
            latest_src = max(latest_src, getmtime(src))
        for dst in self.dsts:
            earliest_dst = min(earliest_dst, getmtime(dst))
        return earliest_dst >= latest_src

class Target(_Initer):
    class Error(Exception):
        def __str__(self):
            return '%s: %s' % (self[0], self[1])
    dependencies = ()
    uptodates = ()
    _been_called = False
    def get_been_called(self):
        return self.__class__._been_called
    def set_been_called(self, value):
        self.__class__._been_called = value
    been_called = property(get_been_called, set_been_called)
    def __str__(self):
        return self.__class__.__name__
    #def __repr__(self):
    #    return '<%s>' % self
    def validate_tree(klass):
        targets = klass.get_targets()
        uptodates = klass.get_uptodates()
        try:
            deps = klass.dependencies
        except AttributeError:
            pass
        else:
            for dep in deps:
                if not targets.has_key(dep):
                    raise ValueError('invalid dependency: %s' % dep)
                targets[dep].validate_tree()
        try:
            utds = klass.uptodates
        except AttributeError:
            pass
        else:
            for utd in utds:
                if not uptodates.has_key(utd):
                    raise ValueError('invalid uptodate')
    validate_tree = classmethod(validate_tree)
    def call_uptodate(self, klassname):
        uptodates = self.get_uptodates()
        try:
            klass = uptodates[klassname]
        except KeyError:
            raise self.Error(str(self), 'no such uptodate: %s' % klassname)
        return klass(self.basedir)()
    def call_dependency(self, klassname):
        targets = self.get_targets()
        try:
            klass = targets[klassname]
        except KeyError:
            raise self.Error(str(self), 'no such dependency: %s' % klassname)
        klass(self.basedir)()
    def __call__(self, *args):
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
        try:
            self.run()
        except Exception, e:
            raise self.Error(str(self), e)
        else:
            self.verbose('done.')
            self.been_called = True
    def run(self):
        pass
    def verbose(self, *args):
        from sys import stdout
        stdout.write('%s: ' % self)
        stdout.write(' '.join([str(s) for s in args]))
        stdout.write('\n')
        stdout.flush()
    def get_targets():
        import __main__
        if not hasattr(__main__, '_targets_cache'):
            targets = {}
            for name, obj in vars(__main__).items():
                if not name.startswith('_') \
                   and obj is not Target \
                   and isinstance(obj, type(Target)) \
                   and issubclass(obj, Target):
                    targets[name] = obj
            setattr(__main__, '_targets_cache', targets)
        return getattr(__main__, '_targets_cache')
    get_targets = staticmethod(get_targets)
    def get_uptodates():
        import __main__
        if not hasattr(__main__, '_uptodates_cache'):
            uptodates = {}
            for name, obj in vars(__main__).items():
                if not name.startswith('_') \
                   and obj is not Uptodate \
                   and isinstance(obj, type(Uptodate)) \
                   and issubclass(obj, Uptodate):
                    uptodates[name] = obj
            setattr(__main__, '_uptodates_cache', uptodates)
        return getattr(__main__, '_uptodates_cache')
    get_uptodates = staticmethod(get_uptodates)

    def get_files(self, files=None, noglob=False):
        from glob import glob
        from os.path import join
        if noglob:
            glob = lambda x: [x]
        if not files:
            files = self.files
        filelist = []
        for entry in files:
            s = glob(join(self.basedir, entry))
            filelist.extend(s)
        return filelist
    def join(self, *path):
        from os.path import join
        return join(self.basedir, *path)
    def spawn(self, cmd, outfile=None, errfile=None):
        from os import WIFSIGNALED, WTERMSIG, WEXITSTATUS
        try:
            from subprocess import call
            of = ef = None
            if outfile:
                of = open(outfile, 'w')
            if errfile == outfile:
                ef = of
            elif errfile:
                ef = open(errfile, 'w')
            rc = call(cmd, shell=True, stdout=of, stderr=ef, bufsize=0)
            if rc < 0:
                raise ValueError('signal', abs(rc))
            return rc
        except ImportError:
            from popen2 import Popen3
            pcmd = cmd
            if outfile:
                pcmd = '%s >"%s"' % (pcmd, outfile)
            if errfile == outfile:
                pcmd = '%s 2>&1' % pcmd
            elif errfile:
                pcmd = '%s 2>"%s"' % (pcmd, errfile)
            print pcmd
            rc = Popen3(pcmd, capturestderr=False, bufsize=0).wait()
            if WIFSIGNALED(rc):
                raise ValueError('signal', WTERMSIG(rc))
            return WEXITSTATUS(rc)
    def remove(self, *entries, **kwargs):
        from os import remove
        from os.path import isdir, isfile, islink
        from shutil import rmtree
        noglob = kwargs.has_key('noglob') and kwargs['noglob']
        for fname in self.get_files(entries, noglob):
            if isfile(fname) or islink(fname):
                remove(fname)
            elif isdir(fname):
                rmtree(fname)
    def copy(self, srcs, dst, noglob=False):
        from glob import glob
        from os.path import join
        from shutil import copy2
        if noglob:
            glob = lambda x: [x]
        if type(srcs) not in (type(()), type([])):
            srcs = [srcs]
        for fname in self.get_files(srcs, noglob):
            copy2(fname, join(self.basedir, dst))
    def copytree(self, srcdir, dstdir):
        from os.path import exists, isdir, join
        if not exists(srcdir):
            raise os.error(2, "No such file or directory: %s" % srcdir)
        elif not isdir(srcdir):
            raise os.error(20, "Not a directory: %s" % srcdir)
        dirs = [self.basedir]
        while dirs:
            dir = dirs[0]
            del dirs[0]
            self.mkdir(join(dstdir, dir))
            for (dirpath, dirnames, filenames) in walk(join(srcdir, dir)):
                for subdirname in dirnames:
                    dirs.append(join(dir, subdirname))
                for filename in filenames:
                    self.copy(
                        join(srcdir, dir, filename),
                        join(dstdir, dir, filename),
                        noglob=True
                    )
    def mkdir(klass, path):
        from os import mkdir, remove
        from os.path import dirname, isdir, isfile, islink
        if islink(path) or isfile(path):
            remove(path)
            klass.mkdir(path)
        elif not isdir(path):
            klass.mkdir(dirname(path))
            mkdir(path)
    mkdir = classmethod(mkdir)
    def tar(self, tarname, root, *files, **kwargs):
        from tarfile import open
        from os.path import join
        if kwargs.has_key('exclude'):
            exctest = lambda t, e=kwargs['exclude']: [v for v in e if t.endswith(v)]
            filter = lambda t, e=exctest: not e(t.name) and t or None
            exclusion = lambda t, e=exctest: e(t)
        else:
            filter = None
            exclusion = None
        file = open(tarname, 'w:gz')
        for filename in files:
            try:
                file.add(join(root, filename), filename, filter=filter)
            except TypeError:
                file.add(join(root, filename), filename, exclude=exclusion)
        file.close()
    def untar(self, tarname, root, *files):
        from tarfile import open
        from os.path import join
        from os import pardir, sep
        file = open(tarname, 'r:gz')
        fileset = []
        for member in file.getmembers():
            if member.name.startswith(sep) or member.name.startswith(pardir):
                pass
            elif not files or member.name in files:
                fileset.append(member)
        for fileinfo in fileset:
            file.extract(fileinfo, path=(root or ""))
        file.close()
    def zip(self, zipname, root, *files):
        from zipfile import ZipFile
        from os.path import join
        file = ZipFile(zipname, 'w')
        for filename in files:
            file.write(join(root, filename), filename)
        file.close()
    def unzip(self, zipname, root, *files):
        from zipfile import ZipFile
        from os.path import dirname, join
        from os import pardir, sep
        file = open(zipname, 'r')
        fileset = []
        for member in file.namelist():
            if member.startswith(sep) or member.startswith(pardir):
                pass
            elif not files or member in files:
                fileset.append(member)
        for member in fileset:
            dname = join(root, member)
            self.mkdir(dirname(dname))
            dfile = open(dname, 'wb')
            dfile.write(file.read(member))
        file.close()

def pymain():
    from sys import argv
    # need to "import __main__" and not "from __main__ import Default"
    import __main__
    targets = []
    # map arguments into classes above: e.g. 'all' into All
    if len(argv) == 1:
        targets.append(__main__.Default)
    else:
        all_targets = Target.get_targets()
        for name in argv[1:]:
            try:
                obj = all_targets[name.capitalize()]
            except KeyError:
                raise SystemExit('Error: unknown target: %s' % name)
            else:
                if not issubclass(obj, Target):
                    raise SystemExit('Error: unknown target: %s' % name)
                targets.append(obj)
    # validate the dependency tree, make sure that all are subclasses of
    # Target
    for target in targets:
        try:
            target.validate_tree()
        except ValueError, e:
            raise SystemExit('Error: %s: %s' % (str(target()), e))
    # run all the targets in the tree of each argument
    for target in targets:
        try:
            target()()
        except target.Error, e:
            raise SystemExit(e)

# standard targets

class Help(Target):
    """This information"""
    def run(self):
        for name, obj in sorted(self.get_targets().items()):
            print '%-20s  %s' % (obj.__name__.lower(), obj.__doc__ or "")

class Clean(Target):
    """Clean directories and files used by the build"""
    files = ()
    def run(self):
        self.remove(*self.files)

class InitDirs(Target):
    """Create initial directories"""
    files = ()
    def run(self):
        from os.path import join
        for dirname in self.files:
            self.mkdir(join(self.basedir, dirname))

class Init(Target):
    """Initialize the build"""
    dependencies = ("InitDirs",)

class Compile(Target):
    """Do something interesting"""
    # meant to be overriden

class Build(Target):
    """The primary build"""
    dependencies = ("Init", "Compile")

class Dist(Target):
    """The primary packaging"""
    dependencies = ("Build",)
    # may be overriden

# default target
class All(Target):
    """Do it all"""
    dependencies = ("Clean", "Dist")

class Default(Target):
    dependencies = ("Dist",)

if __name__ == '__main__':
    pymain()
