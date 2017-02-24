#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Tasks plugin for PyCompile."""

from ..args import Arguments
from ..path import Path
from ..exception import Error
from ..base import Initer
from ..iterators import Iterator, FileIterator
from ..helper import Subcommand
from ._base import Task

class PyCompile(Task):
    """Compile Python source files.
constructor arguments:
PyCompile(*files, dest=<DIR>, version='2')"""
    arguments = Arguments(
        Arguments.List('files', types=(Iterator, Path, str), cast=FileIterator),
        Arguments.Keyword('version', default='2'),
    ) + Initer.basearguments

    def run(self):
        """Compile Python source files."""
        import py_compile
        import sys
        fileset = self.get_files()
        # pylint: disable=no-member
        version = self.args.version
        if version[:1] == sys.version[:1]:  # compile inline
            for fname in fileset:
                if fname.isdir:
                    self.compile_dir(self.join(fname))
                else:
                    self.compile_file(self.join(fname))
        else:
            if version[:1] == '2':
                cmd = 'python2'
            elif version[:1] == '3':
                cmd = 'python3'
            else:
                cmd = 'python'
            for item in fileset:
                self.compile_file_ext(self.join(item), cmd)

    def compile_file_ext(self, fname, python):
        """Compile a file or files in a directory."""
        import sys
        if fname.isdir:
            files = tuple(fn for fn in fname if fn.isfile)
            subdirs = tuple(fn for fn in fname if fn.isdir)
        else:
            files = (fname,)
            subdirs = ()
        cmd = (python, '-c', 'import sys; from py_compile import compile; ' +
               '[compile(s) for s in sys.argv[1:]]'
              ) + files
        try:
            proc = Subcommand(cmd)
        except Error:
            exc = sys.exc_info()[1]
            if exc.args[0] == 'ENOENT':
                self.logger.error('%s: Error with %s: %s',
                                  self.__class__.__name__, cmd, exc.args[1])
            else:
                raise
        else:
            if proc.returncode != 0:
                raise Error('count not compile files with %s', cmd)
        for fname in subdirs:
            self.compile_file_ext(fname, python)

    def compile_file(self, fname):
        """Compile (pyc) a file."""
        self.logger.debug('py_compile.compile(%s)', fname)
        import py_compile
        py_compile.compile(fname.value)

    def compile_dir(self, dirname):
        """Recurse through the directory tree."""
        for fname in dirname:
            if fname.isdir:
                self.compile_dir(fname)
            else:
                self.compile_file(fname)

PyCompile.register()
