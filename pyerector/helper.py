#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import os
from sys import version

__all__ = [
    'normjoin',
    'spawn',
]

class Verbose(object):
    from os import linesep as eoln
    from sys import stdout as stream
    prefix = ''
    def __init__(self, state=False):
        from os import environ
        self.state = bool(state)
        if 'PYERECTOR_PREFIX' in environ:
            self.prefix = environ['PYERECTOR_PREFIX'].decode('UTF-8')
    def __bool__(self):
        return self.state
    __nonzero__ = __bool__
    def on(self):
        self.state = True
    def off(self):
        self.state = False
    def write(self, msg):
        if self.prefix != '':
            self.stream.write(u(self.prefix))
            self.stream.write(u(': '))
        self.stream.write(u(msg))
        self.stream.write(u(self.eoln))
        self.stream.flush()
    def __call__(self, *args):
        if self.state:
            self.write(u(' ').join([u(str(s)) for s in args]))

# helper routines
def normjoin(*args):
    return os.path.normpath(os.path.join(*args))

if version < '3':
    def u(x):
        from codecs import unicode_escape_decode
        return unicode_escape_decode(x)[0]
else:
    def u(x):
        return x

class Subcommand(object):
    try:
        import subprocess
    except ImportError:
        raise NotImplemented("Earlier than Python 2.6 is unsupported")
    PIPE = subprocess.PIPE
    def __init__(self, cmd, wdir=os.curdir, env={}, wait=True,
                 stdin=None, stdout=None, stderr=None):
        import subprocess
        self.func = self.call_subprocess
        assert isinstance(cmd, tuple), "must supply tuple as command"
        if (len(cmd) == 1 and
            (isinstance(cmd[0], tuple) or isinstance(cmd, list))):
            self.cmd = tuple(cmd[0])
        else:
            self.cmd = cmd
        self.wdir = wdir
        self.env = env
        self.proc = None
        self.infile = stdin
        self.outfile = stdout
        self.errfile = stderr
        self.stdin = self.stdout = self.stderr = None
        self.returncode = None
        self.func()
        if wait:
            self.wait()

    def __del__(self):
        self.close()
        if self.returncode is None and self.proc is not None:
            self.proc.terminate()
            try:
                os.kill(self.proc.pid, 0) # check if there
            except:
                pass
            else:
                self.proc.kill()
            self.proc = None

    def close(self):
        if hasattr(self.infile, 'lower'):
            self.stdin.close()
        self.stdin = None
        if hasattr(self.outfile, 'lower'):
            self.stdout.close()
        self.stdout = None
        if hasattr(self.errfile, 'lower'):
            self.stderr.close()
        self.stderr = None

    def poll(self):
        rc = self.proc.poll()
        if rc != -1:
            self.returncode = rc
        return (self.returncode is not None)
    def wait(self):
        if self.stdin:
            self.stdin.close()
        self.returncode = self.proc.wait()
        return self.returncode

    def _process_returncode(self, rc):
        if self.func is self.call_subprocess:
            self.returncode = rc
        elif hasattr(os, 'WIFSIGNALED') and os.WIFSIGNALED(rc):
            self.returncode = -os.WTERMSIG(rc)
        elif os.WIFEXITED(rc):
            self.returncode = os.WEXITSTATUS(rc)
        else:
            self.returncode = 0

    def call_subprocess(self):
        from subprocess import Popen
        realenv = os.environ.copy()
        realenv.update(self.env)
        ifl = of = ef = None
        if hasattr(self.infile, 'write'):
            ifl = self.infile
        elif self.infile == self.PIPE:
            ifl = self.PIPE
        elif hasattr(self.infile, 'lower'):
            ifl = open(self.infile, 'r')
        else:
            ifl = None
        if hasattr(self.outfile, 'read'):
            of = self.outfile
        elif self.outfile == self.PIPE:
            of = self.PIPE
        elif hasattr(self.outfile, 'lower'):
            of = open(self.outfile, 'w')
        else:
            of = None
        if self.errfile == self.outfile:
            ef = of
        elif hasattr(self.errfile, 'read'):
            ef = self.errfile
        elif self.errfile == self.PIPE:
            ef = self.PIPE
        elif hasattr(self.errfile, 'lower'):
            ef = open(self.errfile, 'w')
        else:
            ef = None
        (self.stdin, self.stdout, self.stderr) = (ifl, of, ef)
        shellval = not isinstance(self.cmd, tuple)
        from . import verbose
        verbose("Popen(%s, shell=%s, stdin=%s, stdout=%s, stderr=%s, bufsize=0, env=%s)" % (self.cmd, shellval, ifl, of, ef, realenv))
        proc = Popen(self.cmd, shell=shellval,
                     stdin=ifl, stdout=of, stderr=ef,
                     bufsize=0, env=realenv)
        self.proc = proc
        if ifl == self.PIPE:
            self.stdin = proc.stdin
        if of == self.PIPE:
            self.stdout = proc.stdout
        if ef == self.PIPE:
            self.stderr = proc.stderr

