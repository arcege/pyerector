#!/usr/bin/python
"""Tasks plugin for Unittest."""

from ._base import Base
from ..args import Arguments
from ..path import Path
from ..exception import Error
from ..base import Task
from ..helper import Subcommand
from ..variables import V

class Unittest(Task, Base):
    """Call Python unit tests found.
constructor arguments:
Unittest(*modules, path=())"""
    path = ()
    arguments = Arguments(
        Arguments.List('modules', types=(Path, str), cast=str),
    )

    def run(self):
        """Call the 'unit-test.py' script in the package directory with
serialized parameters as the first argument string."""
        import logging
        import sys
        # pylint: disable=no-member
        modules = self.args.modules
        bdir = Path(__file__).dirname.dirname
        sfile = bdir + 'unit-test.py'
        if not sfile.exists:
            raise Error(self, 'unable to find unittest helper program')
        # create a parameter file with a serialized set of the arguments
        params = repr({
            'modules': modules,
            'path': self.path,
            'verbose': bool(self.logger.isEnabledFor(logging.INFO)),
            'quiet': bool(self.logger.isEnabledFor(logging.ERROR)),
        })
        # call python <scriptname> <params>
        Subcommand((sys.executable, str(sfile), params),
                   wdir=V['basedir'],
                   env={'COVERAGE_PROCESS_START': '/dev/null'})

Unittest.register()
