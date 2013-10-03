#!/usr/bin/python

import os
from ..helper import Subcommand
from ..exception import Error

class Base(object):
    def __init__(self, rootdir=os.curdir):
        self.rootdir = rootdir
        self.current_info()
    def __str__(self):
        return self.name
    def vcs_check(dir=os.curdir):
        return False
    vcs_check = staticmethod(vcs_check)
    def current_info(self):
        pass

class VCS_Base(Base):
    def checkout(self, url, destdir=os.curdir):
        rc = Subcommand(
                (self.prog, 'checkout', url, destdir),
                wait=True
        )
    def update(self, destdir=None, rev=None):
        if rev is None:
            revopts = ()
        else:
            revopts = ('-r', str(rev))
        rc = Subcommand(
                (self.prog, 'update') + revops + (destdir or self.rootdir,),
                wait=True,
                stderr=Subcommand.PIPE,
        )
        rc.wait()
        if rc.returncode < 0:
            errput = rc.stderr.read().rstrip()
            raise Error(self, 'signal received %d' % abs(rc.returncode))
        elif rc.returncode > 0:
            errput = rc.stderr.read().rstrip()
            raise Error(self, 'error %d: %s' % (abs(rc.returncode), errput))

class DVCS_Base(Base):
    def checkout(self, url, destdir=None):
        rc = Subcommand(
                (self.prog, 'clone', url, destdir or self.reposdir),
                wait=True
        )
    def update(self, source=None, rev=None):
        if rev is None:
            revopts = ()
        else:
            revopts = ('-r', str(rev))
        if source is None:
            sourcearg = ()
        else:
            sourcearg = (source,)
        rc = Subcommand(
                (self.prog, 'pull', '-u') + revopts + sourcearg,
                wait=True,
                wdir=self.rootdir,
                stderr=Subcommand.PIPE,
        )
        rc.wait()
        if rc.returncode < 0:
            raise Error(self, 'signal received %d' % abs(rc.returncode))
        elif rc.returncode > 0:
            errput = rc.stderr.read().rstrip()
            raise Error(self, 'error %d: %s' % (abs(rc.returncode), errput))
