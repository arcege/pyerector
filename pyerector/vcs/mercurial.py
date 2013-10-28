#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.
"""Mercurial(hg) based version control hooks."""

import os

from ..helper import Subcommand
from .base import DVCS_Base
from ..variables import Variable

__all__ = [
    'Mercurial'
]


class Mercurial(DVCS_Base):
    """Version control class for Mercurial."""
    name = 'mercurial'
    prog = 'hg'
    directory = '.hg'

    def current_info(self):
        """Retrieve information from the workarea."""
        proc = Subcommand(
            (self.prog, 'identify', '--id', '--branch', '--tags'),
            wait=True,
            wdir=self.rootdir,
            stdout=Subcommand.PIPE,
            stderr=os.devnull
        )
        hgout = proc.stdout.read().decode('UTF-8')
        if proc.returncode == 0:
            parts = hgout.rstrip().split()
            try:
                parts[1]
            except IndexError:
                parts.append(None)
            try:
                parts[2]
            except IndexError:
                parts.append(None)
            Variable('hg.version', parts[0])
            Variable('hg.branch', parts[1])
            Variable('hg.tags', parts[2])

Mercurial.register()

