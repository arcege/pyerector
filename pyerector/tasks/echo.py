#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Tasks plugin for Chmod."""

from ._base import Task

class Echo(Task):
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
        self.display(text)

Echo.register()
