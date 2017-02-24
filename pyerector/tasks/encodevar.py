#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Tasks plugin for EncodeVar."""

from ..args import Arguments
from ..variables import V
from ._base import Task

class EncodeVar(Task):
    """Encode a Variable using zlib and base64.
To Decode, use:
def Decode(data):
    from zlib import decompress
    try:
        from base64 import b64decode
    except ImportError:
        from binascii import a2b_base64
        accum = []
        for line in data.rstrip().split('\n'):
            accum.append(a2b_base64(line))
        bdata = ''.join(accum)
    else:
        bdata = b64decode(data)
    return decompress(data)
"""
    arguments = Arguments(
        Arguments.Keyword('source'),
        Arguments.Keyword('dest'),
    )

    def run(self):
        """Encode a string."""
        # pylint: disable=no-member
        V(self.args.dest).value = self.encode(V(self.args.source).value)

    @staticmethod
    def encode(data):
        """Perform the actual encoding."""
        from zlib import compress
        from base64 import b64encode
        return b64encode(compress(data))

EncodeVar.register()
