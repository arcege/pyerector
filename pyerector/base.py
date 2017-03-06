#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.
"""Define the primary constructs for use within the package; namely
Initer (base class), Sequential, Parallel.
"""

import logging
from sys import version
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
from .helper import Exclusions, DISPLAY
from .args import Arguments
from .path import Path
from .execute import get_current_stack, PyThread
from .register import registry
from .exception import Abort, Error
from .config import Config
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
        from .iterators import Iterator, FileIterator
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
        from .iterators import Iterator
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

    def display(self, msg, *args, **kwargs):
        """Display a message at the DISPLAY log level, which should
be above the level that the --quiet option would set."""
        from logging import getLevelName
        self.logger.log(DISPLAY, msg, *args, **kwargs)


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
        from .iterators import Mapper
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
        from .iterators import Mapper
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

