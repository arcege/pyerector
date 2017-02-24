#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Tasks plugin for Copy."""

from ._base import IteratorTask

class Remove(IteratorTask):
    """Remove a file or directory tree.
constructor arguments:
Remove(*files)"""

    def dojob(self, name, context=None):
        self.logger.info('remove(%s)', name)
        name.remove()

Remove.register()
