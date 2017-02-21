#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Tasks plugin for Chmod."""

from ._base import Base
from ..args import Arguments
from ..path import Path
from ..base import Iterator, Task
from ..iterators import FileIterator

class Chmod(Task, Base):
    """Change file permissions.
constructor arguments:
Chmod(*files, mod=0666)"""
    arguments = Arguments(
        Arguments.List('files', types=(Iterator, Path, str), cast=FileIterator),
        Arguments.Keyword('mode', types=int, default=int('666', 8), cast=int),
    )

    def run(self):
        """Change the permissions on the files."""
        files = self.get_files()
        # pylint: disable=no-member
        mode = self.args.mode
        for fname in files:
            self.asserttype(fname, (Path, str), 'files')
            self.logger.info('chmod(%s, %s0', fname, mode)
            path = self.join(fname)
            path.chmod(mode)
            if isinstance(fname, Path):
                fname.refresh()

Chmod.register()
