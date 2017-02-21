#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.
"""Define the base classes for the various version control systems,
including centralized (VCS) and decentralized (DVCS)."""

import os
from ..path import Path
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
    def vcs_check(cls, srcdir=Path(os.curdir)):
        """Check directory tree in reverse for one of the registered
Base subclasses.  Return the subclass that 'fits'.  If the directory
attribute is None, use that subclass as default."""
        if not isinstance(srcdir, Path):
            srcdir = Path(srcdir)
        srcdir = srcdir.real
        default = None
        klasses = cls.registered()
        while srcdir.value not in ('', os.sep, os.curdir):
            for icls in klasses:
                if icls.directory is None:
                    default = icls
                elif (srcdir + icls.directory).isdir:
                    return icls
            srcdir = srcdir.dirname
        return default

    def current_info(self):
        """To be overridden."""
        pass


class VCSBase(Base):
    """Base class for VCS classes (e.g. Subversion)."""
    prog = None

    def checkout(self, url, destdir=Path(os.curdir)):
        """Perform a checkout."""
        Subcommand(
            (self.prog, 'checkout', url, str(destdir)),
            wait=True
        )

    def update(self, destdir=None, rev=None):
        """Update the workarea from the repository."""
        if rev is None:
            revopts = ()
        else:
            revopts = ('-r', str(rev))
        proc = Subcommand(
            (self.prog, 'update') + revopts + \
                    (destdir and str(destdir) or str(self.rootdir),),
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


class DVCSBase(Base):
    """Base class for DVCS classes (e.g. Mercurial)."""
    prog = None

    def checkout(self, url, destdir=None):
        """Perform a checkout (clone)."""
        Subcommand(
            (self.prog, 'clone', url,
             destdir and str(destdir) or str(self.rootdir)),
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
            wdir=str(self.rootdir),
            stderr=Subcommand.PIPE,
        )
        proc.wait()
        if proc.returncode < 0:
            raise Error(self, 'signal received %d' % abs(proc.returncode))
        elif proc.returncode > 0:
            errput = proc.stderr.read().rstrip()
            raise Error(self, 'error %d: %s' % (abs(proc.returncode), errput))

