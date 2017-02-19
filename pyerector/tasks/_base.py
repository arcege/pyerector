#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Base class for registering tasks."""

import os
from ..register import Register

class Base(object):
    """Setup the structure of the subclasses."""
    _register = Register()

    @classmethod
    def register(cls):
        """Register this class for easier retrieval later."""
        cls._register[cls.__name__] = cls
    @classmethod
    def registered(cls):
        """Retrieve the registered classes."""
        return sorted([cls._register[name] for name in cls._register],
                      key=lambda x: x.__name__)

    def __init__(self, rootdir=os.curdir):
        self.rootdir = rootdir

    def __str__(self):
        return self.__class__.__name__

