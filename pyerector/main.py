#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import logging
import os
import sys
import traceback
from .exception import Abort, Error, extract_tb
from .helper import Timer
from . import display, noop
from .register import registry
from .base import Target, Task
from .version import Version
from .variables import V, Variable

__all__ = [
    'PyErector', 'pymain',
]

# the main program, an instance to be called by pyerect program
class PyErector(object):
    try:
        import argparse
        parser = argparse.ArgumentParser(
            description='Pyerector build system; '
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
        import optparse
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
        self.basedir = None
        self.targets = []
        try:
            self.arguments(args or sys.argv[1:])
            self.validate_targets()
            self.run()
        except Abort:
            raise SystemExit(1)
    def arguments(self, args):
        global noop
        args = self.parser.parse_args(args)
        if isinstance(args, tuple):
            args, arglist = args
            args.targets = arglist
        # check --verbose before --version
        if args.notimer:
            import pyerector
            pyerector.noTimer.on()
        if args.verbose:
            logging.getLogger().setLevel(logging.INFO)
        if args.DEBUG:
            logging.getLogger().setLevel(logging.DEBUG)
        # check --quiet after --verbose
        if args.quiet:
            logging.getLogger().setLevel(logging.ERROR)
        if args.noop:
            noop.on()
        if args.version:
            if logging.getLogger().isEnabledFor(logging.INFO):
                display('%s %s\n' % (Version.release, Version.version))
            else:
                display('%s\n' % Version.release)
            raise SystemExit
        if args.directory:
            self.basedir = args.directory
        elif self.basedir is None:
            self.basedir = self.progdir
        V['basedir'] = Variable('basedir', self.basedir)
        if args.targets:
            self.targets = []
            all_targets = registry.get('Target')
            for name in args.targets:
                if '=' in name:  # variable assignment?
                    var, val = name.split('=', 1)
                    Variable(var.strip(), val.strip())
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
    def handle_error(self, text=''):
        if True: #debug:
            t, e, tb = sys.exc_info()
            if tb:
                exclist = extract_tb(tb, valid_classes=(Target, Task))
                traceback.print_list(exclist)
            lines = traceback.format_exception_only(t, e)
            for line in lines:
                display(line.rstrip())
        else:
            e = sys.exc_info()[1]
            if text:
                raise SystemExit('%s: %s' % (text, e))
            else:
                raise SystemExit(str(e))
    def validate_targets(self):
        # validate the dependency tree, make sure that all are subclasses of
        # Target, validate all Uptodate values and all Task values
        for target in self.targets:
            try:
                target.validate_tree()
            except ValueError:
                self.logger.exception('Validation')
    def run(self):
        timer = Timer()
        # run all targets in the tree of each argument
        with timer:
            for target in self.targets:
                try:
                    self.logger.debug('PyErector.basedir = %s', self.basedir)
                    target(basedir=self.basedir)()
                except Abort:
                    break  # handled already internally
                except ValueError:
                    self.logger.exception(self.__class__.__name__)
                except KeyboardInterrupt:
                    raise Abort
                except AssertionError:
                    self.handle_error('AssertionError')
                except Error:
                    self.logger.exception(self.__class__.__name__)
        import pyerector
        if pyerector.noTimer:
            display('Done.')
        else:
            display('Done. (%0.3f)' % timer)

pymain = PyErector

