#!/usr/bin/python

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
    for vcs in vcs_set:
        if vcs.vcs_check():
            break
    else:
        raise RuntimeError('no version control found')
    return vcs(*args, **kwargs)

