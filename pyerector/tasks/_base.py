#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Base class for registering tasks."""

import logging

from ..execute import get_current_stack
from ..args import Arguments
from ..exception import Abort, Error
from ..path import Path
from ..register import Register
from ..variables import V
from ..base import Initer
from ..iterators import FileMapper, Iterator

class Task(Initer):
    """A representation of a unit of work.  Generally performs Python code
directly, either as one of the standard tasks or through the API.  The
run() method is meant to be overridden.
"""
    _register = Register()

    @classmethod
    def register(cls):
        """Register this class for easier retrieval later."""
        cls._register[cls.__name__] = cls
    @classmethod
    def registered(cls):
        """Retrieve the registered classes."""
        return sorted([cls._register[name] for name in cls._register],
                      key=lambda x: x.__name__)

    args = []

    def __str__(self):
        return self.__class__.__name__

    def __call__(self, *args, **kwargs):
        myname = self.__class__.__name__
        self.logger.debug('%s.__call__(*%s, **%s)', myname, args, kwargs)
        stack = get_current_stack()
        stack.push(self)  # push me onto the execution stack
        try:
            if self.has_arguments:
                self.args = self.arguments.process(
                    args, kwargs, existing=self.baseargs
                )
            else:
                self.handle_args(args, kwargs)
            if V['pyerector.noop']:
                self.logger.warning('Calling %s(*%s, **%s)',
                                    myname, args, kwargs)
                return
            try:
                returncode = self.run()
            except (KeyError, ValueError, TypeError,
                    RuntimeError, AttributeError):
                raise
            except Abort:
                raise  # reraise
            except Error:
                self.logger.exception('Exception in %s.run', myname)
                raise Abort
            except Exception:
                logging.getLogger('pyerector').exception('Exception')
                raise Abort
        finally:
            stack.pop()
        if returncode:
            raise Error(str(self), 'return error = %s' % returncode)
        else:
            self.logger.info('%s: done.', myname)

    def run(self):
        """To be overridden."""

    def handle_args(self, args, kwargs):
        """Put the arguments into their proper places."""
        if (hasattr(self, 'args') and not self.args) or args:
            if len(args) == 1 and isinstance(args[0], Iterator):
                self.args = args[0]
            else:
                self.args = tuple(args)
        if kwargs:
            # pylint: disable=attribute-defined-outside-init
            self.kwargs = dict(kwargs)


class IteratorTask(Task):
    """Perform operations on a iterator of files."""

    arguments = Arguments(
        Arguments.List('files', types=(Iterator, Path, str), cast=Iterator),
    ) + Initer.basearguments

    # pylint: disable=no-self-use
    def setup(self):
        """Return a context (dict) with anything that needs to be set up
before the iterator is called."""
        return {}

    def run(self):
        """Call the job for each file in the arguments."""
        if self.has_arguments:
            files = self.get_files()
        else:
            files = self.get_files(arg='args')
        context = self.setup()
        for name in files:
            self.logger.debug('%s: calling dojob with %s', self.__class__.__name__, name)
            self.dojob(name, context)

    def dojob(self, name, context=None):
        """To be overridden."""


class MapperTask(Task):
    """Perform operations on a mapper of files."""
    arguments = Arguments(
        Arguments.List('files', types=(Iterator, Path, str), cast=Iterator),
        Arguments.Keyword('dest', types=(Path, str), cast=Path),
    ) + Initer.basearguments

    mapperclass = None

    # pylint: disable=no-self-use
    def setup(self):
        """Return a context (dict) with anything that needs to be set up
before the iterator is called."""
        return {}

    def run(self):
        """Call the job for each file and dest in the arguments."""
        # we need to include inside the function since iterators wouldn't have loaded yet
        if self.mapperclass is None:
            mapcls = FileMapper
        elif isinstance(self.mapperclass, Iterator):
            mapcls = self.mapperclass
        else:
            raise Error('expecting Iterator or Mapper for mapperclass')
        context = self.setup()
        # pylint: disable=no-member
        fmap = mapcls(self.get_files(), destdir=self.args.dest)
        for (sname, dname) in fmap:
            self.dojob(sname, dname, context)

    def dojob(self, sname, dname, context):
        """To be overridden."""

