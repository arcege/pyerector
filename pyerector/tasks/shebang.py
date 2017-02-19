#!/usr/bin/python
"""Tasks plugin for Shebang."""

from ._base import Base
from ..args import Arguments
from ..path import Path
from ..base import Iterator, Task
from ..iterators import FileIterator, FileMapper
from .copy import Copy

# is the Base unnecessary given that Copy is also a subclass?
class Shebang(Copy, Base):
    """Replace the shebang string with a specific pathname.
constructor arguments:
Shebang(*files, dest=<DIR>, token='#!', program=<FILE>)"""
    token = '#!'
    arguments = Arguments(
        Arguments.List('files', types=(Iterator, Path, str), cast=FileIterator),
        Arguments.Keyword('dest', types=(Path, str), cast=Path),
        Arguments.Keyword('program', types=(Path, str), noNone=True),
    )
    def run(self):
        """Replace the shebang string with a specific pathname."""
        self.logger.info('starting Shebang')
        # pylint: disable=no-member
        program = self.args.program
        srcs = self.get_files()
        # pylint: disable=no-member
        dest = self.args.dest
        try:
            from io import BytesIO as StringIO
        except ImportError:
            from StringIO import StringIO
        if dest is None:
            dest = Path()
        for sname, dname in FileMapper(srcs, destdir=dest):
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
