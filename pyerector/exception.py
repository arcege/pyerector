#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.
"""Exceptions and exception frame handling for displaying traceback
objects "appropriately" (with the class name).
"""

import sys
import linecache


class Abort(Exception):
    """Roll back to the PyErector call."""


class Error(Exception):
    """Error within pyerector to raise."""
    def __str__(self):
        return ': '.join([str(a) for a in self.args])

    def __format__(self, format_spec):
        value = format(str(self), format_spec)
        if isinstance(format_spec, unicode):
            return unicode(value)
        else:
            return value

# basically reproducing the extract_tb call but with conditionally
# prepending the class name to the function/method name if the class
# is a subclass of Target or Task (handled externally)
# pylint: disable=dangerous-default-value,invalid-name
def extract_tb(tb, limit=None, last_object=[None], valid_classes=()):
    """Return a list of the traceback objects, just as
traceback.extract_tb(), but the function/method name would be augmented
with the class name if a subclass of one of the valid_class entries."""
    if limit is None:
        if hasattr(sys, 'tracebacklimit'):
            limit = getattr(sys, 'tracebacklimit')
    flist = []
    level = 0
    fself = None
    while tb is not None and (limit is None or level < limit):
        frame = tb.tb_frame
        lineno = frame.f_lineno
        code = frame.f_code
        filename = code.co_filename
        name = code.co_name
        linecache.checkcache(filename)
        line = linecache.getline(filename, lineno, frame.f_globals)
        if line:
            line = line.strip()
        else:
            line = None
        if 'self' in frame.f_locals:
            fself = frame.f_locals['self']
            if not isinstance(fself, valid_classes):
                fself = None
            if fself is not None and last_object[0] != fself:
                last_object[0] = fself
            elif fself is None and last_object[0] is not None:
                fself = last_object[0]
        elif last_object[0] is not None:
            fself = last_object[0]
        del frame  # delete the frame reference so there is circular reference
        if fself:
            name = '%s.%s' % (fself.__class__.__name__, name)
        flist.append((filename, lineno, name, line))
        tb = tb.tb_next
        level += 1
    del flist[:1]  # first should be handle_error, unfortunately
    return flist

