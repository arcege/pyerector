#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import sys
from . import verbose, debug, noop
from .register import registry
from .base import Initer, Target

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
    except ImportError:
        import optparse
        parser = optparse.OptionParser(description='Pyerector build system')
        del optparse
        parser.add_option('--directory', '-d', help='base directory')
        parser.add_option('--dry-run', '-N', dest='noop', action='store_true',
                          help='do not perform operations')
        parser.add_option('--verbose', '-v', action='store_true',
                          help='more verbose output')
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
        if args.verbose:
            verbose.on()
        if args.noop:
            noop.on()
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
        if debug:
            raise
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
        # run all targets in the tree of each argument
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

pymain = PyErector

