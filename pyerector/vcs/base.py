#!/usr/bin/python
# Copyright @ 2012-2015 Michael P. Reilly. All rights reserved.
"""Define the base classes for the various version control systems,
including centralized (VCS) and decentralized (DVCS)."""

import os
from ..helper import Subcommand
from ..exception import Error
from ..register import Register


class Base(object):
    """Setup the structure of the subclasses."""
    name = None
    directory = ''
    _register = Register()

    @classmethod
    def register(cls):
        """Register this class for easier retrieval later."""
        cls._register[cls.name] = cls
    @classmethod
    def registered(cls):
        """Retrieve the registered classes."""
        return sorted([cls._register[name] for name in cls._register],
                      key=lambda x: x.__name__)

    def __init__(self, rootdir=os.curdir):
        self.rootdir = rootdir
        self.current_info()

    def __str__(self):
        return self.name

    # used by the package to see which VCS system to use
    @classmethod
    def vcs_check(cls, srcdir=os.curdir):
        """Check directory tree in reverse for one of the registered
Base subclasses.  Return the subclass that 'fits'.  If the directory
attribute is None, use that subclass as default."""
        srcdir = os.path.realpath(os.path.normpath(srcdir))
        default = None
        klasses = cls.registered()
        while srcdir not in ('', os.sep):
            for c in klasses:
                if c.directory is None:
                    default = c
                elif os.path.isdir(os.path.join(srcdir, c.directory)):
                    return c
            srcdir = os.path.dirname(srcdir)
        return default

    def current_info(self):
        """To be overridden."""
        pass


class VCS_Base(Base):
    """Base class for VCS classes (e.g. Subversion)."""
    prog = None

    def checkout(self, url, destdir=os.curdir):
        """Perform a checkout."""
        Subcommand(
            (self.prog, 'checkout', url, destdir),
            wait=True
        )

    def update(self, destdir=None, rev=None):
        """Update the workarea from the repository."""
        if rev is None:
            revopts = ()
        else:
            revopts = ('-r', str(rev))
        proc = Subcommand(
            (self.prog, 'update') + revopts + (destdir or self.rootdir,),
            wait=True,
            stderr=Subcommand.PIPE,
        )
        proc.wait()
        if proc.returncode < 0:
            proc.stderr.read().rstrip()
            raise Error(self, 'signal received %d' % abs(proc.returncode))
        elif proc.returncode > 0:
            errput = proc.stderr.read().rstrip()
            raise Error(self, 'error %d: %s' % (abs(proc.returncode), errput))


class DVCS_Base(Base):
    """Base class for DVCS classes (e.g. Mercurial)."""
    prog = None

    def checkout(self, url, destdir=None):
        """Perform a checkout (clone)."""
        Subcommand(
            (self.prog, 'clone', url, destdir or self.rootdir),
            wait=True
        )

    def update(self, source=None, rev=None):
        """Update the workarea (pull)."""
        if rev is None:
            revopts = ()
        else:
            revopts = ('-r', str(rev))
        if source is None:
            sourcearg = ()
        else:
            sourcearg = (source,)
        proc = Subcommand(
            (self.prog, 'pull', '-u') + revopts + sourcearg,
            wait=True,
            wdir=self.rootdir,
            stderr=Subcommand.PIPE,
        )
        proc.wait()
        if proc.returncode < 0:
            raise Error(self, 'signal received %d' % abs(proc.returncode))
        elif proc.returncode > 0:
            errput = proc.stderr.read().rstrip()
            raise Error(self, 'error %d: %s' % (abs(proc.returncode), errput))

