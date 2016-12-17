#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.
"""No version control hooks."""

from .base import VCS_Base
from ..variables import Variable

__all__ = [
    'NoVCS',
]

class NoVCS(VCS_Base):
    """Version control class for no version control."""
    name = 'none'
    directory = None

NoVCS.register()
