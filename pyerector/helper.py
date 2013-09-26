#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import fnmatch
import logging
import os
from sys import version, exc_info
import traceback

from .exception import Error

__all__ = [
    'Exclusions',
    'normjoin',
    'Subcommand',
]

# helper routines
def normjoin(*args):
    if not args:
        args = ('',)
    return os.path.normpath(os.path.join(*args))

if version < '3':
    def u(x):
        from codecs import unicode_escape_decode
        return unicode_escape_decode(x)[0]
else:
    def u(x):
        return x

class Exclusions(set):
    """A list of exclusion patterns."""
    defaults = set(
        ('*.pyc', '*~', '.*.swp', '.git',
         '.hg', '.svn', 'CVS', '__pycache__')
    )
    def __init__(self, items=(), usedefaults=True):
        if isinstance(items, Exclusions):
            if usedefaults != items.usedefaults:
                usedefaults = items.usedefaults
            items = set(items)
        elif not isinstance(items, (str, set, tuple, list, type(None))):
            raise TypeError('Exclusions: expecting str, set, tuple or list')
        if isinstance(items, str): # proper casting
            items = (str,)
        if items:
            initialset = set(items)
        else:
            initialset = set()
        self.usedefaults = usedefaults
        if usedefaults:
            initialset |= self.defaults
        super(Exclusions, self).__init__(initialset)
    def match(self, str):
        values = [v for v in self if fnmatch.fnmatchcase(str, v)]
        return len(values) > 0
    @classmethod
    def set_defaults(cls, items=(), reset=False):
        """Change or reset the defaults for all instances."""
        if reset and hasattr(cls, 'real_defaults'):
            cls.defaults = cls.real_defaults
            del cls.real_defaults
            return
        elif reset:
            return
        if not hasattr(cls, 'real_defaults'):
            cls.real_defaults = cls.defaults
        if not isinstance(items, (set, tuple, list)):
            raise TypeError('Exclusions: expecting set, tuple or list')
        cls.defaults = set(items)

class Subcommand(object):
    """Handles some of the subprocess details."""
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
        logging.debug('starting %s.__del__()', self.__class__.__name__)
        self.close()
        if self.returncode is None and self.proc is not None:
            self.proc.terminate()
            try:
                os.kill(self.proc.pid, 0) # check if there
            except:
                pass
            else:
                self.proc.kill()
            self.proc.wait()
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

    def terminate(self):
        assert self.proc is not None, 'subprocess not spawned'
        return self.proc.terminate()
    def kill(self):
        assert self.proc is not None, 'subprocess not spawned'
        return self.proc.kill()
    def poll(self):
        assert self.proc is not None, 'subprocess not spawned'
        rc = self.proc.poll()
        if rc is not None:
            self.returncode = rc
        return (self.returncode is not None)
    def wait(self):
        assert self.proc is not None, 'subprocess not spawned'
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
        logging.debug('Popen(%s, shell=%s, cwd=%s, stdin=%s, stdout=%s, stderr=%s, bufsize=0, env=%s)', self.cmd, shellval, self.wdir, ifl, of, ef, self.env)
        try:
            proc = Popen(self.cmd, shell=shellval, cwd=self.wdir,
                         stdin=ifl, stdout=of, stderr=ef,
                         bufsize=0, env=realenv)
        except (IOError, OSError):
            t, e, tb = exc_info()
            if e.args[0] == 2: # ENOENT
                raise Error('ENOENT', 'Program not found')
            else:
                raise
        self.proc = proc
        if ifl == self.PIPE:
            self.stdin = proc.stdin
        if of == self.PIPE:
            self.stdout = proc.stdout
        if ef == self.PIPE:
            self.stderr = proc.stderr

class Timer(object):
    def __init__(self):
        self.starttime = None
        self.duration = None
    def __repr__(self):
        name = self.__class__.__name__
        if self.starttime is not None:
            return '<%s started>' % name
        elif self.duration is not None:
            return '<%s duration: %0.3f>' % (name, self.duration)
        else:
            return '<%s unstarted>' % name
    def now(self):
        from time import time
        return time()
    def start(self):
        if self.starttime is not None:
            raise RuntimeError('cannot start more than once without stopping')
        self.starttime = self.now()
    def stop(self):
        if self.starttime is None:
            raise RuntimeError('cannot stop without starting')
        self.duration = self.now() - self.starttime
        self.starttime = None
    def __enter__(self):
        self.start()
    def __exit__(self, etype, evalue, etb):
        self.stop()
    def __float__(self):
        if self.duration is not None:
            return float(self.duration)
        return 0.0
    def __int__(self):
        return int(float(self))

def extract_stack(stack):
    #from .base import stack  # do not move outside of this routine
    t, e, tb = exc_info()
    lines = stack.extract() + traceback.format_exception_only(t, e)
    return ''.join(lines)
class LogFormatter(logging.Formatter):
    logPrefix = None
    def format(self, record):
        newrecord = super(LogFormatter, self).format(record)
        if self.logPrefix is None:
            try:
                prefix = os.environ['PYERECTOR_PREFIX']
            except (AttributeError,KeyError):
                prefix = ''
            self.logPrefix = prefix
        else:
            prefix = self.logPrefix
        if prefix:
            if isinstance(newrecord, logging.LogRecord):
                message = '%s: %s' % (prefix, newrecord.message)
            else:
                message = '%s: %s' % (prefix, newrecord)
        elif isinstance(newrecord, logging.LogRecord):
            message = newrecord.message
        else:
            message = newrecord
        return message
    def formatException(self, exc_info):
        from .exceptions import extract_tb
        t, e, tb = exc_info
        exc = traceback.format_exception_only(t, e)
        st = traceback.format_list(extract_tb(tb))
        return ''.join(st + exc)
class LogExecFormatter(LogFormatter):
    def formatException(self, exc_info):
        from .base import stack  # do not move outside of this method
        t, e, tb = exc_info
        lines = stack.extract() + traceback.format_exception_only(t, e)
        return ''.join(lines).rstrip()
def init_logging(deflevel=logging.WARNING, message='%(message)s'):
    global DISPLAY
    def setup(name, handlerklass, formatterklass,
              deflevel=deflevel, message=message):
        f = formatterklass(message)
        h = handlerklass()
        h.setFormatter(f)
        l = logging.getLogger(name)
        l.addHandler(h)
        l.propagate = False
        return l
    logging.basicConfig(level=deflevel, message=message)
    DISPLAY = logging.ERROR + 5
    logging.addLevelName(level=DISPLAY, levelName='DISPLAY')
    setup('pyerector', logging.StreamHandler, LogFormatter)
    setup('pyerector.execute', logging.StreamHandler, LogExecFormatter)
def display(msg, *args, **kwargs):
    logging.getLogger('pyerector.execute').log(DISPLAY, msg, *args, **kwargs)

