#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Tasks plugin for Mkdir."""

from ..path import Path
from ._base import IteratorTask

class Mkdir(IteratorTask):
    """Recursively create directories.
constructor arguments:
Mkdir(*files)"""

    def dojob(self, name, context=None):
        """Make directories."""
        self.logger.debug('mkdir.name = %s', repr(name))
        self.mkdir(name)

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
