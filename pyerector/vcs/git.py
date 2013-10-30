#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.
"""Git based version control hooks."""

import os

from ..helper import Subcommand
from .base import DVCS_Base
from ..variables import Variable

__all__ = [
    'Git',
]


class Git(DVCS_Base):
    """Version control class for Git."""
    name = 'git'
    prog = 'git'
    directory = '.git'

    def current_info(self):
        """Retrieve information from the workarea."""
        proc = Subcommand(
            (self.prog, 'log', '--max-count=1', '--format=%h'),
            wait=True,
            stdout=Subcommand.PIPE,
            stderr=os.devnull
        )
        gitout = proc.stdout.read().decode('UTF-8')
        if proc.returncode == 0:
            Variable('git.version', gitout.strip())
            git_version = gitout.strip()
        else:
            git_version = None
        proc = Subcommand(
            (self.prog, 'branch', '--no-color', '--list'),
            wait=True,
            stdout=Subcommand.PIPE,
            stderr=os.devnull
        )
        gitout = proc.stdout.read().decode('UTF-8')
        if proc.returncode == 0:
            for line in gitout.rstrip(os.linesep).split(os.linesep):
                if line.startswith('*'):
                    if line[2:].strip() != '(no branch)':
                        Variable('git.branch', line[2:].strip())
        if git_version:
            proc = Subcommand(
                (self.prog, 'tag', '--contains', git_version),
                wait=True,
                stdout=Subcommand.PIPE,
                stderr=os.devnull
            )
            gitout = proc.stdout.read().decode('UTF-8')
            if proc.returncode == 0:
                if gitout.strip():
                    Variable('git.tag', gitout.strip())

# this is used by the package to get the primary class
VCS_class = Git
Git.register()

