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

def VCS(*args, **kwargs):
    from ..variables import V
    try:
        basedir = V['basedir'].value
    except KeyError:
        basedir = os.curdir
    for vcs in vcs_set:
        if vcs.vcs_check(dir=basedir):
            break
    else:
        raise RuntimeError('no version control found')
    return vcs(*args, **kwargs)

