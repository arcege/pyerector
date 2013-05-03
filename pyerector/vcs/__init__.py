#!/usr/bin/python

import os

from .git import *
from .mercurial import *
from .subversion import *

vcs_set = [
    Git,
    Mercurial,
    Subversion,
]

__all__ = [
    'VCS'
]

basedir = os.curdir

def VCS(*args, **kwargs):
    for vcs in vcs_set:
        if vcs.vcs_check(dir=basedir):
            break
    else:
        raise RuntimeError('no version control found')
    return vcs(*args, **kwargs)

