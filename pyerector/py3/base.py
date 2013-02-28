#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import sys
from ..exception import Error
from ..metaclass import IniterMetaClass

__all__ = [
    'Uptodate', 'Target', 'Task',
]

class Base(metaclass = IniterMetaClass):
    def rewrap_exception(self):
        e = sys.exc_info()
        if isinstance(e[1], Error):
            msg = '%s:%s' % (self, e[1].args[0])
            v =  e[1].args[1]
        else:
            msg = str(self)
            v = e[1]
        raise Error(msg, v) from e[1]

