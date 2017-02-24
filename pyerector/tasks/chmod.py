#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Tasks plugin for Chmod."""

from ..args import Arguments
from ..path import Path
from ._base import IteratorTask

class Chmod(IteratorTask):
    """Change file permissions.
constructor arguments:
Chmod(*files, mod=0666)"""
    arguments = Arguments(
        Arguments.Keyword('mode', types=int, default=int('666', 8), cast=int),
    ) + IteratorTask.arguments

    def setup(self):
        """Create a context with the arguments."""
        return {
            # pylint: disable=no-member
            'mode': self.args.mode,
        }

    def dojob(self, name, context=None):
        """Change the mode and update the Path instance."""
        self.logger.info('chmod(%s, 0%s)', name, context['mode'])
        name.chmod(context['mode'])
        if isinstance(name, Path):
            name.refresh()

Chmod.register()
