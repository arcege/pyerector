#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.
"""Define the underlying base class for Initer as a metaclass instance
for Python 2.x.
The syntax for metaclass declarations is different between Python 2.x and
Python 3.x."""

from ..metaclass import IniterMetaClass

# pylint: disable=too-few-public-methods
class Base(object):
    """Baseclass with metaclass declaration."""
    __metaclass__ = IniterMetaClass

