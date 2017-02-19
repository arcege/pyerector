#!/usr/bin/python
"""Tasks plugin for Chmod."""

from ._base import Base
from ..args import Arguments
from ..path import Path
from ..base import Task
from ..helper import DISPLAY

class Echo(Task, Base):
    """Display a message, arguments are taken as with logger (msg, *args).
This is displayed by the logging module, but at the internal 'DISPLAY'
level created in pyerector.helper."""
    msgs = ()

    def run(self):
        """Display messages."""
        args = self.get_args('msgs')
        if args:
            msg, rest = args[0], args[1:]
            text = msg % rest
        else:
            text = ''
        self.logger.log(DISPLAY, text)

Echo.register()
