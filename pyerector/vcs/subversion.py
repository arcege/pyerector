#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.
"""Subversion based version control hooks."""

import os

from .base import VCSBase
from ..helper import Subcommand
from ..variables import Variable

__all__ = [
    'Subversion',
]


class Subversion(VCSBase):
    """Version control class for Subversion."""
    name = 'subversion'
    prog = 'svn'
    directory = '.svn'

    def find_dotsvn(self):
        """Find the .svn directory."""
        from ..path import Path
        if isinstance(self.rootdir, Path):
            # pylint: disable=no-member
            svndir = self.rootdir.abs
        else:
            svndir = Path(self.rootdir).abs
        while svndir != os.sep and svndir != os.curdir:
            if (svndir + '.svn').isdir:
                return svndir
            svndir = svndir.dirname
        return None

    def current_info(self):
        """Retrieve information from the workarea."""
        dotsvn = self.find_dotsvn()
        if dotsvn is None:
            return
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
                    self.set_based_on_Revision(line)
                elif line.startswith('URL: '):
                    self.set_based_on_URL(line)
                elif line.startswith('Last Changed Author: '):
                    self.set_based_on_Author(line)
                elif line.startswith('Last Changed Date: '):
                    self.set_based_on_Date(line)

    @staticmethod
    def set_based_on_Revision(line):
        """Set the svn.version variable."""
        pos = line.split(': ')
        Variable('svn.version', pos[1].strip())

    @staticmethod
    def set_based_on_URL(line):
        """Set either the svn.branch or svn.tags variables."""
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

    @staticmethod
    def set_based_on_Author(line):
        """Set the svn.user variable."""
        parts = line.split(': ')
        Variable('svn.user', parts[1].strip())

    @staticmethod
    def set_based_on_Date(line):
        """Set the svn.date variable."""
        parts = line.split(': ')
        Variable('svn.date', parts[1].strip())


Subversion.register()

