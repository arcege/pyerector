#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Tasks plugin for Copy."""

import re
import sys

from ..args import Arguments
from ..exception import Error
from ..variables import VariableSet
from ._base import MapperTask

class Tokenize(MapperTask):
    """Replace tokens found in tokenmap with their associated values in
each file.
constructor arguments:
Tokenize(*files, dest=None, tokenmap=VariableSet())"""
    arguments = Arguments(
        Arguments.Keyword('tokenmap', types=VariableSet, default=VariableSet()),
    ) + MapperTask.arguments

    def update_tokenmap(self, tokenmap):
        """To be overridden."""

    def setup(self):
        """Update tokens and create regexp."""
        # pylint: disable=no-member
        tokenmap = self.args.tokenmap
        self.update_tokenmap(tokenmap)
        # we need the closure to properly pass the tokenmap
        def repltoken(match):
            """Replace."""
            self.logger.debug('repltoken found %s', match.group(0))
            result = tokenmap.get(match.group(0))
            return result is not None and str(result) or ''
        tokens = gen_token_re(tokenmap)
        self.logger.debug('Tokenize.patt = %s', str(tokens.pattern))
        return {
            'repltoken': repltoken,
            'tokenmap': tokenmap,
            'tokens': tokens,
        }

    def dojob(self, sname, dname, context):
        """Perform the task against the src/dst files."""
        try:
            realcontents = sname.open('rt').read()
        except TypeError:
            raise Error('%s: %s' % (sname, sys.exc_info()[1]))
        alteredcontents = context['tokens'].sub(
            context['repltoken'], realcontents
        )
        if alteredcontents != realcontents:
            dname.open('wt').write(alteredcontents)
        else:
            self.logger.info("Tokenize: no change to %s", dname)

def quote(string):
    """Quote the regexp special characters."""
    return string.replace('\\', r'\\').replace('.', r'\.')\
                 .replace('$', r'\$').replace('(', r'\(')\
                 .replace(')', r'\)').replace('|', r'\|')

def gen_token_re(tokenmap):
    """Generate a regular expression for the tokenmap keys."""
    return re.compile(
        r'(%s)' % '|'.join(quote(k) for k in tokenmap),
        re.MULTILINE
    )

Tokenize.register()
