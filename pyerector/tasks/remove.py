#!/usr/bin/python
"""Tasks plugin for Copy."""

from ._base import Base
from ..args import Arguments
from ..path import Path
from ..base import Initer, Iterator, Task
from ..iterators import FileIterator

class Remove(Task, Base):
    """Remove a file or directory tree.
constructor arguments:
Remove(*files)"""
    arguments = Arguments(
        Arguments.List('files', types=(Iterator, Path, str), cast=FileIterator),
    ) + Initer.basearguments

    def run(self):
        """Remove a file or directory tree."""
        files = self.get_files()
        for name in files:
            self.asserttype(name, (Path, str), 'files')
            fname = self.join(name)
            self.logger.info('remove(%s)', fname)
            fname.remove()

Remove.register()
