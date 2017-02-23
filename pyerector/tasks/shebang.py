#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Tasks plugin for Shebang."""

try:
    from io import BytesIO as StringIO
except ImportError:
    from StringIO import StringIO

from ._base import Base
from ..args import Arguments
from ..path import Path
from ..base import MapperTask
from ..iterators import FileIterator, FileMapper
from .copy import Copy

# is the Base unnecessary given that Copy is also a subclass?
class Shebang(Copy, Base):
    """Replace the shebang string with a specific pathname.
constructor arguments:
Shebang(*files, dest=<DIR>, token='#!', program=<FILE>)"""
    token = '#!'
    arguments = Arguments(
        Arguments.Keyword('program', types=(Path, str), noNone=True),
    ) + MapperTask.arguments

    def dojob(self, sname, dname, context):
        import os
        import shutil
        inf = sname.open()
        outf = StringIO()
        first = inf.readline()
        if first.startswith(self.token):
            if ' ' in first:
                wsp = first.find(' ')
            else:
                wsp = first.find(os.linesep)
            first = first.replace(first[len(self.token):wsp], program)
            outf.write(first)
        else:
            outf.write(first)
        shutil.copyfileobj(inf, outf)
        inf.close()
        outf.seek(0)
        inf = dname.open('w')
        shutil.copyfileobj(outf, inf)

Shebang.register()
