#!/usr/bin/python

import os

from ..helper import Subcommand
from .base import DVCS_Base
from ..variables import Variable

__all__ = [
    'Git',
]

class Git(DVCS_Base):
    name = 'git'
    prog = 'git'
    # used by the package to see which VCS system to use
    def vcs_check(dir=os.curdir):
        return os.path.isdir(os.path.join(dir, '.git'))
    vcs_check = staticmethod(vcs_check)
    def current_info(self):
        rc = Subcommand(
                (self.prog, 'log', '--max-count=1', '--format=%h'),
                wait=True,
                stdout=Subcommand.PIPE,
                stderr=os.devnull
        )
        rc.wait()
        gitout = rc.stdout.read().decode('UTF-8')
        if rc == 0:
            Variable('git.version', gitout.strip())
            git_version = gitout.strip()
        else:
            git_version = None
        rc = Subcommand(
                (self.prog, 'branch', '--no-color', '--list'),
                wait=True,
                stdout=Subcommand.PIPE,
                stderr=os.devnull
        )
        rc.wait()
        gitout = rc.stdout.read().decode('UTF-8')
        if rc == 0:
            for line in gitout.rstrip(os.linesep).split(os.linesep):
                if line.startswith('*'):
                    if line[2:].strip() != '(no branch)':
                        Variable('git.branch', line[2:].strip())
        if git_version:
            rc = Subcommand(
                    (self.prog, 'tag', '--contains', git_version),
                    wait=True,
                    stdout=Subcommand.PIPE,
                    stderr=os.devnull
            )
            rc.wait()
            gitout = rc.stdout.read().decode('UTF-8')
            if rc == 0:
                if gitout.strip():
                    Variable('git.tag', gitout.strip())

# this is used by the package to get the primary class
VCS_class = Git
