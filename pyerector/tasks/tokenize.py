#!/usr/bin/python
"""Tasks plugin for Copy."""

from ._base import Base
from ..args import Arguments
from ..path import Path
from ..exception import Error
from ..base import Iterator, Task
from ..iterators import FileIterator, FileMapper, StaticIterator
from ..variables import VariableSet

class Tokenize(Task, Base):
    """Replace tokens found in tokenmap with their associated values in
each file.
constructor arguments:
Tokenize(*files, dest=None, tokenmap=VariableSet())"""
    arguments = Arguments(
        Arguments.List('files', types=(Iterator, Path, str), cast=FileIterator),
        Arguments.Keyword('dest', types=(Path, str), cast=Path),
        Arguments.Keyword('tokenmap', types=VariableSet, default=VariableSet()),
    )

    def update_tokenmap(self):
        """To be overridden."""

    def run(self):
        """Replace tokens found in tokenmap with their associated values."""
        import sys
        files = self.get_files()
        # pylint: disable=no-member
        dest = self.args.dest
        # pylint: disable=no-member
        tokenmap = self.args.tokenmap
        self.update_tokenmap()
        import re

        def repltoken(match, tmap=tokenmap):
            """Replace."""
            self.logger.debug('found %s', match.group(0))
            result = tmap.get(match.group(0))
            return result is not None and str(result) or ''

        def quote(string):
            """Quote special characters."""
            return string.replace('\\', r'\\').replace('.', r'\.')\
                         .replace('$', r'\$').replace('(', r'\(')\
                         .replace(')', r'\)').replace('|', r'\|')
        tokens = re.compile(
            r'(%s)' % '|'.join([quote(k) for k in tokenmap]),
            re.MULTILINE
        )
        self.logger.debug('Tokenize.patt = %s', str(tokens.pattern))
        for (sname, dname) in FileMapper(files, destdir=dest,
                                         iteratorClass=StaticIterator):
            try:
                realcontents = self.join(sname).open('rt').read()
            except TypeError:
                raise Error('%s: %s' % (sname, sys.exc_info()[1]))
            alteredcontents = tokens.sub(repltoken, realcontents)
            if alteredcontents != realcontents:
                self.join(dname).open('wt').write(alteredcontents)
            else:
                self.logger.info("Tokenize: no change to %s", dname)

Tokenize.register()
