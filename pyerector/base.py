#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.
"""Define the primary constructs for use within the package; namely
Initer (base class), Iterator, Mapper, Sequential, Parallel.

Iterator and Mapper have most of their logic defined in iterators.
"""

import logging
import os
from sys import version
import sys
import threading
try:
    reduce
except NameError:
    # pylint: disable=redefined-builtin
    from functools import reduce
if version[0] > '2':  # python 3+
    # pylint: disable=import-error,no-name-in-module
    from .py3.base import Base
else:
    from .py2.base import Base
from .helper import Exclusions, Timer, DISPLAY
from .args import Arguments
from .path import Path
from .execute import get_current_stack, PyThread
from .register import registry
from .exception import Abort, Error
from .config import Config, noTimer
from .variables import V, Variable

__all__ = [
    'Sequential', 'Parallel',
]

# the base class to set up the others


class Initer(Base):
    """Primary base class for everything.  This is responsible for
establishing the common framework for the API, including argument
handling.
"""
    config = Config()  # for backward compatibility only
    # values to propagate to an iterator
    basearguments = Arguments(
        Arguments.Keyword('pattern'),
        Arguments.Keyword('noglob', default=False, types=bool),
        Arguments.Keyword('recurse', default=False, types=bool),
        Arguments.Keyword('fileonly', default=True, types=bool),
        Arguments.Exclusions('exclude'),
    )
    # the arguments attribute should be set by Tasks subclasses,
    # not in the ancesters
    pattern = None
    noglob = False
    recurse = False
    fileonly = True
    exclude = ()

    def __init__(self, *args, **kwargs):
        # pylint: disable=no-member
        self.has_arguments = (
            hasattr(self.__class__, 'arguments') and
            isinstance(self.__class__.arguments, Arguments)
        )
        self.logger = logging.getLogger('pyerector.execute')
        #self.logger.debug('%s.__init__(*%s, **%s)',
        #                  self.__class__.__name__, args, kwargs)
        try:
            basedir = kwargs['basedir']
        except KeyError:
            basedir = None
        else:
            del kwargs['basedir']
        try:
            del kwargs['curdir']
        except KeyError:
            pass
        if self.has_arguments:
            self.baseargs = self.arguments.process(args, kwargs)
        else:
            if args:
                self.args = args
            if kwargs:
                for key in kwargs:
                    setattr(self, key, kwargs[key])
        if basedir is not None:
            V['basedir'] = Path(basedir)

    # __getattr__ was added to allow for users of older
    # releases that have not moved to using args.Arguments
    def __getattr__(self, attr):
        """Simulate pre-1.3.0 interface where arguments were members."""
        from warnings import warn
        if self.has_arguments and hasattr(self.args, attr):
            warn('use Arguments object instead of attributes')
            return getattr(self.args, attr)
        elif not self.has_arguments and hasattr(self, attr):
            warn('use Arguments object instead of attributes')
            return self.__dict__[attr]
        else:
            raise AttributeError(attr)

    # pylint: disable=too-many-branches
    def get_files(self, files=None, arg='files'):
        """Return an Iterator of either a given sequence or the "files"
member.  Iterator attributes define in the class will be propagated to
the Iterator instance.
"""
        # propagate 'noglob' keyword to the interator
        if self.has_arguments:
            if files is None:
                files = self.args[arg]
            try:
                noglob = self.args.noglob
            except AttributeError:
                noglob = False
            try:
                recurse = self.args.recurse
            except AttributeError:
                recurse = False
            try:
                fileonly = self.args.fileonly
            except AttributeError:
                fileonly = True
            try:
                pattern = self.args.pattern
            except AttributeError:
                pattern = None
            try:
                exclude = self.args.exclude
            except AttributeError:
                exclude = Exclusions()
        else:
            if files is None:
                try:
                    files = getattr(self, arg)
                except AttributeError:
                    files = ()
            noglob = self.get_kwarg('noglob', bool)
            recurse = self.get_kwarg('recurse', bool)
            fileonly = self.get_kwarg('fileonly', bool)
            pattern = self.get_kwarg('pattern', str)
            exclude = self.get_kwarg('exclude', (Exclusions, tuple))
            if not isinstance(exclude, Exclusions):
                exclude = Exclusions(exclude)
        # import here to avoid recursive references
        # pylint: disable=cyclic-import
        from .iterators import FileIterator
        fset = FileIterator(noglob=noglob, recurse=recurse,
                            fileonly=fileonly, pattern=pattern,
                            exclude=exclude)
        if isinstance(files, Iterator):
            fset.append(files)
        elif isinstance(files, tuple) and len(files) == 1 and \
             isinstance(files[0], Iterator):
            fset.append(files[0])
        else:
            for entry in files:
                if isinstance(entry, (Path, Iterator)):
                    fset.append(entry)
                else:
                    fset.append(Path(entry))
        self.logger.debug('get_files(%s) = %s', files or "", fset)
        return fset

    def join(self, *path):
        """Normjoin the basedir and the path."""
        self.logger.debug('%s.join(V("basedir"[%s]), *%s)',
                          self, V('basedir'), path)
        return Path(V['basedir'], *path)

    def asserttype(self, value, typeval, valname):
        """Assert that the value is a value type."""
        if isinstance(typeval, type):
            typename = typeval.__name__
        else:
            typename = ' or '.join(t.__name__ for t in typeval)
        text = "Must supply %s to '%s' in '%s'" % (
            typename, valname, self.__class__.__name__
        )
        if isinstance(typeval, (tuple, list)) and callable in typeval:
            lst = list(typeval)[:]
            lst.remove(callable)
            #assert callable(value) or isinstance(value, tuple(lst)), text
            if not callable(value) and not isinstance(value, tuple(lst)):
                raise TypeError(value, text)
        else:
            #assert isinstance(value, typeval), text
            if not isinstance(value, typeval):
                raise TypeError(value, text)

    # pylint: disable=invalid-name
    def get_kwarg(self, name, typeval=None, noNone=False):
        """Return a item in saved kwargs or an attribute of the name name.
If noNone, then raise ValueError if the value is None.
"""
        if self.has_arguments:
            return self.args[name]
        # old scheme
        if hasattr(self, 'kwargs') and name in getattr(self, 'kwargs'):
            value = getattr(self, 'kwargs')[name]
        else:
            value = getattr(self, name)
        if noNone or value is not None:
            self.asserttype(value, typeval, name)
        elif noNone and value is None:
            raise ValueError("no '%s' for '%s'" %
                             (name, self.__class__.__name__))
        return value

    def get_args(self, name):
        """Return the saved argument list or an attribute of the name."""
        if self.has_arguments and name is not None:
            return Iterator(self.args[name])
        elif self.has_arguments:
            return Iterator(self.args)  # as a sequence
        elif hasattr(self, 'args') and getattr(self, 'args'):
            value = getattr(self, 'args')
        elif hasattr(self, name) and getattr(self, name):
            value = getattr(self, name)
        else:
            return ()
        self.asserttype(value, (tuple, list, Iterator), name)
        return value

    @classmethod
    def validate_tree(cls):
        """To be overridden in subclasses."""
        pass  # do nothing, Target will do something with this

    def display(self, msg, *args, **kwargs):
        """Display a message at the DISPLAY log level, which should
be above the level that the --quiet option would set."""
        from logging import getLevelName
        self.logger.log(DISPLAY, msg, *args, **kwargs)


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
        elif isinstance(item, Path):
            path.append(item)
        else:
            path.append(Path(item))
        self.path = tuple(path)

    def _prepend(self, item):
        """Add a string or sequence to the beginning of the pool."""
        if isinstance(item, str):
            item = [Path(item)]
        elif isinstance(item, Path):
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
        return item, result

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


class Sequential(Initer):
    """Class to sequentially call Target or Task instances."""
    items = ()

    def __repr__(self):
        name = self.__class__.__name__[:1]
        return '%s%s' % (name, self.get_args('items'))

    def __iter__(self):
        return iter(self.get_args('items'))

    def __len__(self):
        return len(self.get_args('items'))

    def __bool__(self):
        return len(self) > 0
    __nonzero__ = __bool__

    @staticmethod
    def retrieve(name):
        """Retrieve an instance.  If an instance of a Variable, return None.
If a subclass of Initer, then return an instance of the subclass.
If an instance of Inter, return the object.
If a string (has 'lower' attribute), then find in registry and return an
instance.
Otherwise log an exception and raise Abort error.
"""
        if isinstance(name, Variable):
            return None
        elif isinstance(name, type) and issubclass(name, Initer):
            obj = name()
        elif isinstance(name, Initer):
            obj = name
        elif hasattr(name, 'lower'):
            try:
                kobj = registry[name]
            except (KeyError, AssertionError):
                logging.getLogger('pyerector').exception(
                    'Cannot find %s', name
                )
                raise Abort
            else:
                obj = kobj()
        else:
            logging.getLogger('pyerector.execute').exception(
                'could not retrieve %s', name
            )
            raise Abort
        return obj


    @staticmethod
    def get_exception_message(obj, parent):
        """Generate the appropriate exception message."""
        from .targets import Target
        from .tasks import Task
        if isinstance(obj, Target):
            return 'Exception in %s.dependencies: %s' % (parent, obj)
        elif isinstance(obj, Task):
            return 'Exception in %s.tasks: %s' % (parent, obj)
        elif isinstance(obj, Mapper):
            return 'Exception in %s.uptodates: %s' % (parent, obj)
        else:
            return None

    def __call__(self, *args):
        """Call the items in the list."""
        parent = get_current_stack()[-1]
        abortive = False
        for item in self:
            obj = self.retrieve(item)
            self.logger.debug('Calling %s', obj)
            if obj is None:  # do not process Variable instances
                continue
            if isinstance(obj, Mapper):
                abortive = True
            excmsg = self.get_exception_message(obj, parent)
            try:
                result = obj(*args)
            except Error:
                self.logger.exception(excmsg)
                raise Abort
            else:
                if abortive and not result:
                    return False
        if abortive:
            return True
        else:  # this is just being explicit
            return


class Parallel(Sequential):
    """Class to concurrently call Target or Task instances."""
    def __call__(self, *args):
        """Call the items in the list, in separate threads."""
        parent = get_current_stack()[-1]
        bname = '%s.' % parent
        threads = []
        for item in self:
            obj = self.retrieve(item)
            if obj is None:  # do not process Variable instances
                continue
            thread = PyThread(
                name=bname + str(obj),
                target=obj,
            )
            threads.append(thread)
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        for thread in threads:
            if thread.exception:
                raise Abort
        del threads

