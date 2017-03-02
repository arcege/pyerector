#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Tasks plugin for Spawn."""

from ..args import Arguments
from ..path import Path
from ..exception import Error
from ..helper import Subcommand
from ._base import Task

class Spawn(Task):
    """Spawn a command.
constructor arguments:
Spawn(*cmd, infile=None, outfile=None, errfile=None, env={})"""
    arguments = Arguments(
        Arguments.List('cmd', types=(Path, str), cast=str),
        Arguments.Keyword('infile', types=(Path, str)),
        Arguments.Keyword('outfile', types=(Path, str)),
        Arguments.Keyword('errfile', types=(Path, str)),
        Arguments.Keyword('wdir', types=(Path, str)),
        Arguments.Keyword('env', types=(tuple, dict), default={}, cast=dict),
    )

    def run(self):
        """Spawn a command."""
        # pylint: disable=no-member
        cmd = self.args.cmd
        # pylint: disable=no-member
        infile = self.args.infile
        # pylint: disable=no-member
        outfile = self.args.outfile
        # pylint: disable=no-member
        errfile = self.args.errfile
        # pylint: disable=no-member
        env = self.args.env
        # pylint: disable=no-member
        wdir = self.args.wdir
        infile = infile and self.join(infile) or None
        outfile = outfile and self.join(outfile) or None
        errfile = errfile and self.join(errfile) or None
        proc = Subcommand(cmd, env=env, wdir=wdir,
                          stdin=infile, stdout=outfile, stderr=errfile,
                         )
        if proc.returncode < 0:
            raise Error('Subcommand', '%s signal %d raised' %
                        (str(self), abs(proc.returncode)))
        elif proc.returncode > 0:
            raise Error('Subcommand', '%s returned error = %d' %
                        (str(self), proc.returncode))

Spawn.register()
