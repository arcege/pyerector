#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.
"""No version control hooks."""

from .base import VCSBase

__all__ = [
    'NoVCS',
]

class NoVCS(VCSBase):
    """Version control class for no version control."""
    name = 'none'
    directory = None

NoVCS.register()
