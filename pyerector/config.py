#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import os
import sys
from warnings import warn

from .variables import V

__all__ = [
    'Config',
]

class Config(object):
    """Deprecated, but still provide the same interface, but to variables."""
    def __getattr__(self, variable):
        warn('Config has been deprecated', DeprecationWarning)
        return V[variable]
    def __setattr__(self, variable, value):
        warn('Config has been deprecated', DeprecationWarning)
        V[variable] = value

