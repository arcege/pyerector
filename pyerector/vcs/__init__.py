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
        basedir = V['basedir']
    except KeyError:
        basedir = os.curdir
    for vcs in vcs_set:
        if vcs.vcs_check(srcdir=basedir):
            break
    else:
        raise RuntimeError('no version control found')
    return vcs(*args, **kwargs)
