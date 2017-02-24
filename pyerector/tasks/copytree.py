#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Tasks plugin for CopyTree."""

from ..args import Arguments
from ..path import Path
from ._base import Task
from .copy import Copy

class CopyTree(Task):
    """Copy directory truee. Exclude standard hidden files.
constructor arguments:
CopyTree(srcdir=<DIR>, dstdir=<DIR>, exclude=<defaults>)"""
    arguments = Arguments(
        Arguments.Keyword('srcdir', types=(Path, str), noNone=True, cast=Path),
        Arguments.Keyword('dstdir', types=(Path, str), noNone=True, cast=Path),
        Arguments.Exclusions('exclude'),
    )

    def run(self):
        """Copy a tree to a destination."""
        # pylint: disable=no-member
        srcdir = self.args.srcdir
        # pylint: disable=no-member
        dstdir = self.args.dstdir
        excludes = self.args.exclude
        if not srcdir.exists:
            raise OSError(2, "No such file or directory: " + srcdir)
        elif not srcdir.isdir:
            raise OSError(20, "Not a directory: " + srcdir)
        Copy(srcdir, dest=dstdir, noglob=True, exclude=excludes,
             fileonly=True, recurse=True)()

CopyTree.register()
