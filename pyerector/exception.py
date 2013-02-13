#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

class Error(Exception):
    def __str__(self):
        return str(self.args[0]) + ': ' + str(self.args[1])
    def __format__(self, format_spec):
        if isinstance(self, unicode):
            return unicode(str(self))
        else:
            return str(self)

