#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import sys
import linecache


class Abort(Exception):
    """Roll back to the PyErector call."""


class Error(Exception):
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
def extract_tb(tb, limit=None, last_object=[None], valid_classes=()):
    """Return a list of the traceback objects, just as
traceback.extract_tb(), but the function/method name would be augmented
with the class name if a subclass of one of the valid_class entries."""
    if limit is None:
        if hasattr(sys, 'tracebacklimit'):
            limit = sys.tracebacklimit
    list = []
    n = 0
    fself = None
    while tb is not None and (limit is None or n < limit):
        f = tb.tb_frame
        lineno = f.f_lineno
        co = f.f_code
        filename = co.co_filename
        name = co.co_name
        linecache.checkcache(filename)
        line = linecache.getline(filename, lineno, f.f_globals)
        if line:
            line = line.strip()
        else:
            line = None
        if 'self' in f.f_locals:
            fself = f.f_locals['self']
            if not isinstance(fself, valid_classes):
                fself = None
            if fself is not None and last_object[0] != fself:
                last_object[0] = fself
            elif fself is None and last_object[0] is not None:
                fself = last_object[0]
        elif last_object[0] is not None:
            fself = last_object[0]
        del f  # delete the frame reference so there is circular reference
        if fself:
            name = '%s.%s' % (fself.__class__.__name__, name)
        list.append((filename, lineno, name, line))
        tb = tb.tb_next
        n += 1
    del list[:1]  # first should be handle_error, unfortunately
    return list

