#!/usr/bin/python
# Copyright @ 2012-2015 Michael P. Reilly. All rights reserved.
"""Subversion based version control hooks."""

import os

from .base import VCS_Base
from ..helper import Subcommand
from ..variables import Variable

__all__ = [
    'Subversion',
]


class Subversion(VCS_Base):
    """Version control class for Subversion."""
    name = 'subversion'
    prog = 'svn'
    directory = '.svn'

    def current_info(self):
        """Retrieve information from the workarea."""
        proc = Subcommand(
            (self.prog, 'info', self.rootdir),
            wait=True,
            stdout=Subcommand.PIPE,
            stderr=os.devnull
        )
        svnout = proc.stdout.read().decode('UTF-8')
        if proc.returncode == 0:
            for line in svnout.rstrip(os.linesep).split(os.linesep):
                if line.startswith('Revision: '):
                    pos = line.split(': ')
                    Variable('svn.version', pos[1].strip())
                elif line.startswith('URL: '):
                    parts = line.split(': ')
                    posb = parts[1].find('/branches/')
                    post = parts[1].find('/tags/')
                    if posb != -1:
                        posbe = parts[1].find('/', posb+1) + 1
                        posbn = parts[1].find('/', posbe+1)
                        if posbn == -1:
                            Variable('svn.branch', parts[1][posbe:])
                        else:
                            Variable('svn.branch', parts[1][posbe:posbn])
                    elif post != -1:
                        poste = parts[1].find('/', post+1) + 1
                        postn = parts[1].find('/', poste+1)
                        if postn == -1:
                            Variable('svn.tags', parts[1][poste:])
                        else:
                            Variable('svn.tags', parts[1][poste:postn])
                elif line.startswith('Last Changed Author: '):
                    parts = line.split(': ')
                    Variable('svn.user', parts[1].strip())
                elif line.startswith('Last Changed Date: '):
                    parts = line.split(': ')
                    Variable('svn.date', parts[1].strip())

Subversion.register()

