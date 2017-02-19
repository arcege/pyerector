#!/usr/bin/python
"""Tasks plugin for Mkdir."""

from ._base import Base
from ..args import Arguments
from ..path import Path
from ..base import Initer, Iterator, Task
from ..iterators import FileIterator

class Mkdir(Task, Base):
    """Recursively create directories.
constructor arguments:
Mkdir(*files)"""
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

Mkdir.register()
