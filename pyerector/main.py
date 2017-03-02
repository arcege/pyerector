#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.
"""The main driver of the library.  The PyErector class acts like
a void function, parsing the command-line arguments, setting up the
environment, validating the 'updates', 'dependencies' and 'tasks' members
of all registered targets and then processing the targets and variable
assignments on the command-line.
"""

import logging
import os
import sys
from .exception import Abort, Error
from .path import Path
from .helper import Timer
from .execute import PyThread, Initialization
from .register import registry
from .targets import Target
from .version import Version
from .variables import V

__all__ = [
    'PyErector', 'pymain',
]

# the main program, an instance to be called by pyerect program


class PyErector(object):
    """The main program of the library.  Parses arguments, validates the
calling tree, and starts the PyThread, which calls each target on the
command-line.
"""
    try:
        import argparse
        parser = argparse.ArgumentParser(
            description='PyErector build system; '
            'use the "help" target for more information')
        del argparse
        parser.add_argument('targets', metavar='TARGET', nargs='*',
                            help='\
name of target to call or variable assignment, default target is "default"')
        parser.add_argument('--directory', '-d',
                            help='base directory')
        parser.add_argument('--dry-run', '-N', dest='noop', action='store_true',
                            help='do not perform operations')
        parser.add_argument('--quiet', '-q', action='store_true',
                            help='less output')
        parser.add_argument('--verbose', '-v', action='store_true',
                            help='more verbose output')
        parser.add_argument('--version', '-V', action='store_true',
                            help='show version information')
        parser.add_argument('--notimer', action='store_true',
                            help='do not show timing information')
        parser.add_argument('--DEBUG', action='store_true')
    except ImportError:
        argparse = None
        import optparse
        # pylint: disable=redefined-variable-type
        parser = optparse.OptionParser(
            description='Pyerector build system; '
            'use the "help" target for more information')
        del optparse
        parser.add_option('--directory', '-d', help='base directory')
        parser.add_option('--dry-run', '-N', dest='noop', action='store_true',
                          help='do not perform operations')
        parser.add_option('--quiet', '-q', action='store_true',
                          help='less output')
        parser.add_option('--verbose', '-v', action='store_true',
                          help='more verbose output')
        parser.add_option('--version', '-V', action='store_true',
                          help='show version information')
        parser.add_option('--notimer', action='store_true',
                          help='do not show timing information')
        parser.add_option('--DEBUG', action='store_true')

    def __init__(self, *args):
        program = sys.argv[0]
        self.progdir, self.progname = os.path.split(program)
        if self.progdir == '':
            self.progdir = os.curdir
        else:
            self.progdir = os.path.realpath(self.progdir)
        self.logger = logging.getLogger('pyerector')
        self.targets = []
        # returnstatus should not need mutex since it is only set by the
        # PyErector thread and only read after the thread completes,
        # adding a Condition object seems to cause issues with unittesting
        self.returnstatus = 0  # successfully completed
        try:
            self.arguments(args or sys.argv[1:])
            try:
                assert int(V['pyerector.pool.size']) > 0
            except ValueError:
                raise SystemExit('pyerector.pool.size value is invalid')
            except AssertionError:
                raise SystemExit('pyerector.pool.size must be positive integer')
            self.validate_targets()
            # run through a thread with an initial stack, wait for the thread
            # to finish
            newthread = PyThread(name='PyErector', target=self.run)
            newthread.start()
            newthread.join()
        except KeyboardInterrupt:
            raise SystemExit('Ctrl-C')
        except Abort:
            raise SystemExit(1)
        else:
            raise SystemExit(self.returnstatus)

    def arguments(self, args):
        """Process the command-line arguments.  Not sure if using argparse
or optparse, so handle both.
"""
        args = self.parser.parse_args(args)
        if isinstance(args, tuple):
            args, arglist = args
            args.targets = arglist
        self.process_options(args)
        # process the arguments
        all_targets = registry.get('Target')
        # pylint: disable=no-member
        for name in args.targets:
            if '=' in name:  # variable assignment?
                var, val = name.split('=', 1)
                V[var.strip()] = val.strip()
            else:
                try:
                    obj = all_targets[name.capitalize()]
                except KeyError:
                    raise SystemExit('Error: unknown target: ' + str(name))
                else:
                    if not issubclass(obj, Target):
                        raise SystemExit('Error: unknown target: ' + str(name))
                    self.targets.append(obj)
        if len(self.targets) == 0:
            self.targets.append(registry['Default'])

    def process_options(self, args):
        """Process the options."""
        # check --verbose before --version
        if args.notimer:
            V['pyerector.notimer'] = True
        if args.verbose:
            logging.getLogger().setLevel(logging.INFO)
        if args.DEBUG:
            logging.getLogger().setLevel(logging.DEBUG)
        # check --quiet after --verbose
        if args.quiet:
            logging.getLogger().setLevel(logging.ERROR)
        if args.noop:
            V['pyerector.noop'] = True
        if args.version:
            if logging.getLogger().isEnabledFor(logging.INFO):
                self.logger.log(logging.getLevelName('DISPLAY'),
                                '%s %s', Version.release, Version.version)
            else:
                self.logger.log(logging.getLevelName('DISPLAY'),
                                Version.release)
            raise SystemExit
        if args.directory:
            V['basedir'] = args.directory
        else:
            V['basedir'] = self.progdir

    def validate_targets(self):
        """Validate the dependency tree, make sure that all are subclasses of
Target, validate all Uptodate values and all Task values.
"""
        for target in self.targets:
            try:
                target.validate_tree()
            except ValueError:
                self.logger.exception('Validation')

    def run(self):
        """Call the targets in order."""
        timer = Timer()
        # run all targets in the tree of each argument
        failed = True
        with timer:
            try:
                for target in self.targets:
                    target()()
            except Abort:
                pass
            except ValueError:
                self.logger.exception(self.__class__.__name__)
            except KeyboardInterrupt:
                raise Abort
            except AssertionError:
                self.logger.exception('AssertionError')
            except Error:
                self.logger.exception(self.__class__.__name__)
            else:
                failed = False
        if V['pyerector.notimer']:
            time = ''
        else:
            time = ' (%0.3f)' % timer
        if failed:
            msg = 'Failed.'
        else:
            msg = 'Done.'
        self.logger.warning('%s%s', msg, time)
        if failed:
            # passed to the root thread from (this) PyErector thread
            self.returnstatus = 1

# pylint: disable=invalid-name
pymain = PyErector


class InitMain(Initialization):
    """Initialize the main module."""
    basedir = os.curdir
    def run(self):
        V['basedir'] = Path(self.basedir).real

InitMain()
