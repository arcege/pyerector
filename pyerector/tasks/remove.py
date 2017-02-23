#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Tasks plugin for Copy."""

from ._base import Base
from ..base import Iterator, IteratorTask
from ..iterators import FileIterator

class Remove(IteratorTask, Base):
    """Remove a file or directory tree.
constructor arguments:
Remove(*files)"""

    def dojob(self, name, context):
        self.logger.info('remove(%s)', name)
        name.remove()

Remove.register()
