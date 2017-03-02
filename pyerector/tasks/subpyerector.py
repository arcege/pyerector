#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Tasks plugin for SubPyErector."""

import logging

from ..args import Arguments
from ..path import Path
from ..exception import Error
from ..helper import Subcommand
from ..variables import V
from ._base import Task

class SubPyErector(Task):
    """Call a PyErector program in a different directory.
constructor arguments:
SubPyErector(*targets, wdir=None, prog='pyerect', env={})
Adds PYERECTOR_PREFIX environment variable."""
    arguments = Arguments(
        Arguments.List('targets'),
        Arguments.Keyword('prog', types=(Path, str), default=Path('pyerect'),
                          cast=Path),
        Arguments.Keyword('wdir', types=(Path, str), cast=Path),
        Arguments.Keyword('env', types=(tuple, dict), default={}, cast=dict),
    )

    def run(self):
        """Call a PyErector program in a different directory."""
        # pylint: disable=no-member
        targets = self.args.targets
        # pylint: disable=no-member
        prog = self.args.prog
        # pylint: disable=no-member
        wdir = self.args.wdir
        # pylint: disable=no-member
        env = self.args.env
        # we explicitly add './' to prevent searching PATH
        options = []
        logger = logging.getLogger('pyerector')
        if logger.isEnabledFor(logging.DEBUG):
            options.append('--DEBUG')
        elif logger.isEnabledFor(logging.INFO):
            options.append('--verbose')
        elif logger.isEnabledFor(logging.ERROR):
            options.append('--quiet')
        if V['pyerector.notimer']:
            options.append('--timer')
        if wdir:
            progtouse = (wdir + prog).abs
        else:
            progtouse = (V['basedir'] + prog).abs
        cmd = (str(progtouse),) + tuple(options) + targets
        from os import environ
        evname = 'PYERECTOR_PREFIX'
        if wdir is not None:
            nevname = Path(wdir).basename
        else:
            nevname = V['basedir'].basename
        if evname in environ and environ[evname]:
            env[evname] = '%s: %s' % (environ[evname], str(nevname))
        else:
            env[evname] = str(nevname)
        proc = Subcommand(cmd, wdir=wdir, env=env, wait=True)
        if proc.returncode < 0:
            raise Error('SubPyErector', '%s signal %d raised' %
                        (str(self), abs(proc.returncode)))
        elif proc.returncode > 0:
            raise Error('SubPyErector', '%s returned error = %d' %
                        (str(self), proc.returncode))

SubPyErector.register()
