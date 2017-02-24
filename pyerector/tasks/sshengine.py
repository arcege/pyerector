#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Tasks plugin for Scp and Ssh."""

from ..args import Arguments
from ..path import Path
from ..exception import Error
from ..helper import Subcommand
from ._base import Task

class SshEngine(Task):
    """Superclass for Scp and Ssh since there is the same basic logic."""
    _cmdprog = None
    host = None
    user = None
    identfile = None
    @property
    def remhost(self):
        """Return a user@host representation."""
        ruser = ''
        host = self.get_kwarg('host', str, noNone=True)
        user = self.get_kwarg('user', str)
        if '@' in host:
            ruser, host = host.split('@', 1)
        if user:
            return '%s@%s' % (user, host)
        elif not user and ruser:
            return '%s@%s' % (ruser, host)
        else:
            return host
    def gencmd(self):
        """Return a tuple with the command and arguments."""
        idfile = self.get_kwarg('identfile', (Path, str))
        if idfile:
            identfile = ('-i', str(idfile))
        else:
            identfile = ()
        return (
            self._cmdprog,
            '-o', 'BatchMode=yes',
            '-o', 'ConnectTimeout=10',
            '-o', 'ForwardAgent=no',
            '-o', 'ForwardX11=no',
            '-o', 'GSSAPIAuthentication=no',
            '-o', 'LogLevel=ERROR',
            '-o', 'PasswordAuthentication=no',
            '-o', 'StrictHostkeyChecking=no',
        ) + identfile
    def _run(self, cmd):
        """Backend method to call scp/scp."""
        self.logger.debug('ssh.cmd = %s', cmd)
        proc = Subcommand(cmd,
                          stdout=Subcommand.PIPE,
                          stderr=Subcommand.PIPE,
                          wait=True)
        if proc.returncode:
            raise Error(str(self), proc.stderr.read().rstrip())
        else:
            return proc.stdout.read().rstrip()

class Scp(SshEngine):
    """Spawn an scp command.
constructor arguments:
Scp(*files, dest=<dir>, host=<hostname>, user=<username>, identfile=<filename>,
    recurse=bool, down=bool)"""
    _cmdprog = 'scp'
    files = ()
    dest = None
    recurse = False
    down = True

    def remfile(self, filename):
        """Return the ssh/scp representation of a remote file."""
        return '%s:%s' % (self.remhost, filename)
    def lclfile(self, filename):
        """Return the ssh/scp representation of a local file."""
        return self.join(filename)
    def run(self):
        recurse = self.get_kwarg('recurse', bool)
        dest = self.get_kwarg('dest', (Path, str), noNone=True)
        down = self.get_kwarg('down', bool)
        files = self.get_args('files')
        if down:
            left, right = self.remfile, self.lclfile
        else:
            left, right = self.lclfile, self.remfile
        cmd = self.gencmd()
        if recurse:
            cmd += ('-r',)
        filelst = ()
        for fname in files:
            filelst += (left(fname),)
        filelst += (right(dest),)
        self.logger.info('%s%s', self, filelst)
        self._run(cmd + filelst)

class Ssh(SshEngine):
    """Spawn an ssh command and display the response in verbose mode.
constructor arguments:
Ssh(*cmd, host=<hostname>, user=<username>, identfile=<filename>)
"""
    _cmdprog = 'ssh'
    cmd = ()
    def run(self):
        usercmd = self.get_args('cmd')
        cmd = self.gencmd() + ('-T', self.remhost) + usercmd
        self.logger.info('%s%s', self, usercmd)
        response = self._run(cmd)
        #self.logger.info('Output from %s\n%s', usercmd, response)
        self.logger.warning('\t' + response.rstrip().replace('\n', '\n\t'))

Scp.register()
Ssh.register()
