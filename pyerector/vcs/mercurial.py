#!/usr/bin/python

import os
try:
    import subprocess
except ImportError:
    import popen2
    subprocess = None

from ..helper import Subcommand
from .base import DVCS_Base
from ..variables import Variable

__all__ = [
    'Mercurial'
]

class Mercurial(DVCS_Base):
    name = 'mercurial'
    prog = 'hg'
    # used by the package to see which VCS system to use
    def vcs_check(dir=os.curdir):
        return os.path.isdir(os.path.join(dir, '.hg'))
    vcs_check = staticmethod(vcs_check)
    def current_info(self):
        hg = Subcommand(
                (self.prog, 'identify', '--id', '--branch', '--tags'),
                wait=True,
                stdout=Subcommand.PIPE,
                stderr=os.devnull
        )
        hg.wait()
        hgout = hg.stdout.read()
        if hg.returncode == 0:
            parts = hgout.rstrip().split()
            try:
                parts[1]
            except:
                parts.append(None)
            try:
                parts[2]
            except:
                parts.append(None)
            Variable('hg.version', parts[0])
            Variable('hg.branch', parts[1])
            Variable('hg.tags', parts[2])

# this is used by the package to get the primary class
VCS_class = Mercurial

