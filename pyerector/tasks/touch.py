#!/usr/bin/python
"""Tasks plugin for Touch."""

from ._base import Base
from ..args import Arguments
from ..path import Path
from ..base import Iterator, Task
from ..iterators import FileIterator

class Touch(Task, Base):
    """Create file if it didn't exist already.
constructor arguments:
Touch(*files, dest=None)"""
    arguments = Arguments(
        Arguments.List('files', types=(Iterator, Path, str), cast=FileIterator),
        Arguments.Keyword('dest', types=(Path, str), cast=Path),
    )

    def run(self):
        """Create files, unless they already exist."""
        files = self.get_files()
        # pylint: disable=no-member
        dest = self.args.dest
        for fname in files:
            #self.asserttype(fname, (Path, str), 'files')
            if dest is not None:
                fname = dest + fname
            self.logger.info('touch(%s)', fname)
            self.join(fname).open('a')

Touch.register()
