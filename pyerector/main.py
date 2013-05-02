#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import sys
import traceback
from .exception import Error, extract_tb
from .helper import Timer
from . import display, verbose, debug, noop
from .register import registry
from .base import Initer, Target, Task
from .version import get_version, get_release

__all__ = [
    'PyErector', 'pymain',
]

# the main program, an instance to be called by pyerect program
class PyErector(object):
    try:
        import argparse
        parser = argparse.ArgumentParser(description='Pyerector build system')
        del argparse
        parser.add_argument('targets', metavar='TARGET', nargs='*',
                            help='name of target to call, default is "default"')
        parser.add_argument('--directory', '-d',
                            help='base directory')
        parser.add_argument('--dry-run', '-N', dest='noop', action='store_true',
                            help='do not perform operations')
        parser.add_argument('--verbose', '-v', action='store_true',
                            help='more verbose output')
        parser.add_argument('--version', '-V', action='store_true',
                            help='show version information')
        parser.add_argument('--notimer', action='store_true',
                            help='do not show timing information')
    except ImportError:
        import optparse
        parser = optparse.OptionParser(description='Pyerector build system')
        del optparse
        parser.add_option('--directory', '-d', help='base directory')
        parser.add_option('--dry-run', '-N', dest='noop', action='store_true',
                          help='do not perform operations')
        parser.add_option('--verbose', '-v', action='store_true',
                          help='more verbose output')
        parser.add_option('--version', '-V', action='store_true',
                          help='show version information')
        parser.add_option('--notimer', action='store_true',
                          help='do not show timing information')
    def __init__(self, *args):
        self.basedir = None
        self.targets = []
        self.arguments(args or sys.argv[1:])
        self.validate_targets()
        self.run()
    def arguments(self, args):
        global verbose, noop
        args = self.parser.parse_args(args)
        if isinstance(args, tuple):
            args, arglist = args
            args.targets = arglist
        # check --verbose before --version
        if args.notimer:
            import pyerector
            pyerector.noTimer = True
        if args.verbose:
            verbose.on()
        if args.noop:
            noop.on()
        if args.version:
            if verbose:
                sys.stdout.write('%s %s\n' % (get_release(), get_version()))
            else:
                sys.stdout.write('%s\n' % get_release())
            raise SystemExit
        if args.directory:
            self.basedir = args.directory
            Initer.config.basedir = args.directory
        if args.targets:
            self.targets = []
            all_targets = registry.get('Target')
            for name in args.targets:
                try:
                    obj = all_targets[name.capitalize()]
                except KeyError:
                    raise SystemExit('Error: unknown target: ' + str(name))
                else:
                    if not issubclass(obj, Target):
                        raise SystemExit('Error: unknown target: ' + str(name))
                    self.targets.append(obj)
        else:
            self.targets = [registry['Default']]
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
                self.handle_error('Error')
    def run(self):
        timer = Timer()
        # run all targets in the tree of each argument
        with timer:
            for target in self.targets:
                try:
                    debug('PyErector.basedir =', self.basedir)
                    target(basedir=self.basedir)()
                except ValueError:
                    self.handle_error()
                except KeyboardInterrupt:
                    self.handle_error()
                except AssertionError:
                    self.handle_error('AssertionError')
                except Error:
                    self.handle_error()
        import pyerector
        if pyerector.noTimer:
            verbose.write('Done.')
        else:
            verbose.write('Done. (%0.3f)' % timer)

pymain = PyErector

