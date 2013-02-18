#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

_RCS_VERSION = '$Revision$'

__all__ = [
    'get_version',
]

def get_version():
    return _RCS_VERSION.replace('Revision: ', '').replace('$', '')

