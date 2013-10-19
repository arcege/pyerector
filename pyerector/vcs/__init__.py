#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.
"""Determine the version control system being used."""

import os

from .git import Git
from .mercurial import Mercurial
from .subversion import Subversion

vcs_set = [
    Git,
    Mercurial,
    Subversion,
]

__all__ = [
    'VCS'
]


def VCS(*args, **kwargs):
    """Determine the type of version control and return information
about it.
"""
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

