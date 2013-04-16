#!/usr/bin/python

import os
try:
    import subprocess
except ImportError:
    import popen2
    subprocess = None

from .base import VCS_Base
from ..variables import Variable

__all__ = [
    'Subversion',
]

class Subversion(VCS_Base):
    name = 'subversion'
    prog = 'svn'
    # used by the package to see which VCS system to use
    def vcs_check(dir=os.curdir):
        return os.path.isdir(os.path.join(dir, '.svn'))
    vcs_check = staticmethod(vcs_check)
    def current_info(self):
        svn = Subcommand(
                (self.prog, 'info'),
                wait=True,
                stdout=Subcommand.PIPE,
                stderr=os.devnull
        )
        svn.wait()
        svnout = hg.stdout.read()
        if svn.returncode == 0:
            for line in svnout.rstrip(os.linesep).split(os.linesep):
                if line.startswith('Revision: '):
                    p = line.split(': ')
                    Variable('svn.version', p[1].strip())
                elif line.startswith('URL: '):
                    p = line.split(': ')
                    pb = p[1].find('/branches/')
                    pt = p[1].find('/tags/')
                    if pb != -1:
                        pbe = p[1].find('/', pb+1) + 1
                        pbn = p[1].find('/', bpe+1)
                        if pbn == -1:
                            Variable('svn.branch', p[1][pbe:])
                        else:
                            Variable('svn.branch', p[1][pbe:pbn])
                    elif pt != -1:
                        pte = p[1].find('/', pt+1) + 1
                        ptn = p[1].find('/', pte+1)
                        if ptn == -1:
                            Variable('svn.tags', p[1][pte:])
                        else:
                            Variable('svn.tags', p[1][pte:ptn])

# this is used by the package to get the primary class
VCS_class = Subversion
