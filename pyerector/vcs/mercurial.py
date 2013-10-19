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

    # used by the package to see which VCS system to use
    def vcs_check(srcdir=os.curdir):
        """Check if there is a Mercurial repository present."""
        return os.path.isdir(os.path.join(srcdir, '.hg'))
    vcs_check = staticmethod(vcs_check)

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

# this is used by the package to get the primary class
VCS_class = Mercurial
