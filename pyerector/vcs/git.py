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
    'Git',
]

class Git(VCS_Base):
    name = 'git'
    prog = 'git'
    # used by the package to see which VCS system to use
    def vcs_check(dir=os.curdir):
        return os.path.isdir(os.path.join(dir, '.git'))
    vcs_check = staticmethod(vcs_check)
    def current_info(self):
        git = os.popen('%s log --max-count=1 --format=%%h' % self.prog, 'r')
        gitout = git.read()
        rc = git.close()
        if rc is None or rc == 0:
            Variable('git.version', gitout.strip())
            git_version = gitout.strip()
        else:
            git_version = None
        git = os.popen('%s branch --no-color --list' % self.prog, 'r')
        gitout = git.read()
        rc = git.close()
        if rc is None or rc == 0:
            for line in gitout.rstrip(os.linesep).split(os.linesep):
                if line.startswith('*'):
                    if line[2:].strip() != '(no branch)':
                        Variable('git.branch', line[2:].strip())
        if git_version:
            git = os.popen('%s tag --contains %s' % (self.prog, git_version),
                           'r')
            gitout = git.read()
            rc = git.close()
            if rc is None or rc == 0:
                if gitout.strip():
                    Variable('git.tag', gitout.strip())

# this is used by the package to get the primary class
VCS_class = Git
