#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Superclasses for Tar/Untar, Zip/Unzip and Egg tasks."""

import os

from ..args import Arguments
from ..path import Path
from ..base import Initer
from ..iterators import Iterator, FileIterator
from ._base import Task

class Container(Task):
    """An internal task for subclassing standard classes Tar and Zip."""
    arguments = Arguments(
        Arguments.List('files', types=(Iterator, Path, str), cast=FileIterator),
        Arguments.Keyword('name', types=(Path, str), noNone=True),
        Arguments.Keyword('root', types=(Path, str), default=os.curdir,
                          cast=Path),
    ) + Initer.basearguments

    def run(self):
        """Gather filenames and put them into the container."""
        files = self.get_files()
        # pylint: disable=no-member
        name = self.args.name
        # pylint: disable=no-member
        root = self.args.root
        # pylint: disable=no-member
        excludes = self.args.exclude
        self.logger.debug('Container.run(name=%s, root=%s, excludes=%s)',
                          repr(name), repr(root), repr(excludes))
        self.preop(name, root, excludes)
        toadd = set()
        queue = list(files)
        self.logger.debug('Container.run: files=%s', queue)
        while queue:
            entry = queue[0]
            del queue[0]
            try:
                if isinstance(entry, (Path, str)):
                    self._check_path(Path(entry), toadd, excludes, queue)
                else:
                    if isinstance(entry, Iterator):
                        sequence = iter(entry)
                    else:
                        sequence = root.glob(entry)
                    for fname in sequence:
                        self._check_path(Path(fname), toadd, excludes, queue)
            except TypeError:
                pass
        toadd = sorted(toadd)  # covert set to a list and sort
        self.manifest(name, root, toadd)
        self.contain(name, root, toadd)
        self.postop(name, root, toadd)

    @staticmethod
    def _check_path(fname, toadd, excludes, queue):
        """Ignore excluded files, add directories to the queue, or to the
toadd."""
        if excludes.match(fname):  # if true, ignore
            pass
        elif fname.islink or fname.isfile:
            toadd.add(fname)
        elif fname.isdir:
            queue.extend(fname)  # expand directory listing

    def preop(self, name, root, excludes):
        """To be overridden."""

    def postop(self, name, root, excludes):
        """To be overridden."""

    def manifest(self, name, root, toadd):
        """To be overridden."""

    def contain(self, name, root, toadd):
        """To be overridden."""


class Uncontainer(Task):
    """Super-class for Untar and Unzip."""
    arguments = Arguments(
        Arguments.List('files', types=(Iterator, Path, str), cast=FileIterator),
        Arguments.Keyword('name', types=(Path, str), noNone=True),
        Arguments.Keyword('root', types=(Path, str)),
    )

    def run(self):
        """Extract members from the container."""
        files = self.get_files()
        # pylint: disable=no-member
        name = self.args.name
        # pylint: disable=no-member
        root = self.args.root
        try:
            # pylint: disable=assignment-from-none
            contfile = self.get_file(name)
        except IOError:
            raise ValueError('no such file or directory: %s' % name)
        else:
            # pylint: disable=assignment-from-none
            fileset = self.retrieve_members(contfile, files)
            self.extract_members(contfile, fileset, root)
            contfile.close()

    def get_file(self, name):
        """To be overridden."""

    def extract_members(self, contfile, fileset, root):
        """To be overridden."""

    @staticmethod
    def retrieve_members(contfile, files):
        """To be overridden."""

