#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.
"""Helper routines for the pyerector package.

The Exclusions class can be used by Iterators to prevent matching against
certain file (like .svn, .hg, .git) or patterns (*.pyc, *~).

normjoin runs os.path.normpath(os.path.join(*args), as a convenience
routine.

The Subcommand class handles spawning processes through subprocess.Popen,
but with a bit more backend control (like terminating the process when
the object is deleted).

Initialize the logging system, including setting up module specific
formatters.  It does not change the root ('') logger.
"""

import fnmatch
import logging
import os
from sys import version, exc_info
import traceback
import warnings

from .exception import Error
from .execute import get_current_stack, Initialization

__all__ = [
    'Exclusions',
    'normjoin',
    'Subcommand',
]

# helper routines


def normjoin(*args):
    """Join and normalize the arguments into a pathname."""
    if not args:
        args = ('',)
    return os.path.normpath(os.path.join(*args))


class Exclusions(set):
    """A list of exclusion patterns.
The usedefaults argument can take three values: True (default), False and
None.  A True will augment the set with the 'defaults' values.  A False
will augment with a set containing vcs_names.  And None will not augment
any additional values - this is dangerous when used with the Remove
task."""
    vcs_names = set(('.git', '.hg', '.svn', 'CVS'))
    cruft_patts = set(('*.pyc', '*~', '.*.swp', '__pycache__'))
    defaults = vcs_names | cruft_patts

    def __init__(self, items=(), usedefaults=True):
        if isinstance(items, Exclusions):
            if usedefaults != items.usedefaults:
                usedefaults = items.usedefaults
            items = set(items)
        elif not isinstance(items, (str, set, tuple, list, type(None))):
            raise TypeError('Exclusions: expecting str, set, tuple or list')
        if isinstance(items, str):  # proper casting
            items = (str,)
        if items:
            initialset = set(items)
        else:
            initialset = set()
        self.usedefaults = usedefaults
        super(Exclusions, self).__init__(initialset)

    def match(self, string):
        """Return true if the given string matches one of the patterns
in the set."""
        # augment the possible matches with the defaults
        if self.usedefaults == True:
            matches = self | self.defaults
        elif self.usedefaults == False:
            matches = self | self.vcs_names
        else:
            matches = self
        values = [v for v in matches
                      if fnmatch.fnmatchcase(os.path.basename(string), v)]
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
        subprocess = None
        raise NotImplementedError("Earlier than Python 2.6 is unsupported")
    PIPE = subprocess.PIPE

    def __init__(self, cmd, wdir=os.curdir, env=None, wait=True,
                 stdin=None, stdout=None, stderr=None):
        if env is None:
            env = {}
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
        self.call_subprocess()
        if wait:
            self.wait()

    def __del__(self):
        import traceback
        logging.debug('starting %s.__del__()', self.__class__.__name__)
        self.close()
        if hasattr(self, 'returncode') and hasattr(self, 'proc') and \
                self.returncode is None and self.proc is not None:
            self.proc.terminate()
            try:
                os.kill(self.proc.pid, 0)  # check if there
            except OSError:
                pass
            else:
                self.proc.kill()
            self.proc.wait()
            self.proc = None

    def close(self):
        """Close the open files."""
        if hasattr(self, 'infile') and \
                hasattr(getattr(self, 'infile'), 'lower') and \
                self.stdin is not None:
            self.stdin.close()
        self.stdin = None
        if hasattr(self, 'outfile') and \
                hasattr(getattr(self, 'outfile'), 'lower') and \
                self.stdout is not None:
            self.stdout.close()
        self.stdout = None
        if hasattr(self, 'errfile') and \
                hasattr(getattr(self, 'errfile'), 'lower') and \
                self.stderr is not None:
            self.stderr.close()
        self.stderr = None

    def terminate(self):
        """Send a SIGTERM signal to the process."""
        assert self.proc is not None, 'subprocess not spawned'
        return self.proc.terminate()

    def kill(self):
        """Send a SIGKILL signal to the process."""
        assert self.proc is not None, 'subprocess not spawned'
        return self.proc.kill()

    def poll(self):
        """Return True if the process has finished, setting returncode
if applicable."""
        assert self.proc is not None, 'subprocess not spawned'
        returncode = self.proc.poll()
        if returncode is not None:
            self.returncode = returncode
        return self.returncode is not None

    def wait(self):
        """Wait for the process to complete, and return the exit status."""
        assert self.proc is not None, 'subprocess not spawned'
        if self.stdin:
            self.stdin.close()
        self.returncode = self.proc.wait()
        return self.returncode

    def call_subprocess(self):
        """Call subprocess.Popen and handle the I/O."""
        from subprocess import Popen
        realenv = os.environ.copy()
        realenv.update(self.env)
        if hasattr(self.infile, 'write'):
            ifile = self.infile
        elif self.infile == self.PIPE:
            ifile = self.PIPE
        elif hasattr(self.infile, 'lower'):
            ifile = open(self.infile, 'r')
        else:
            ifile = None
        if hasattr(self.outfile, 'read'):
            ofile = self.outfile
        elif self.outfile == self.PIPE:
            ofile = self.PIPE
        elif hasattr(self.outfile, 'lower'):
            ofile = open(self.outfile, 'w')
        else:
            ofile = None
        if self.errfile == self.outfile:
            efile = ofile
        elif hasattr(self.errfile, 'read'):
            efile = self.errfile
        elif self.errfile == self.PIPE:
            efile = self.PIPE
        elif hasattr(self.errfile, 'lower'):
            efile = open(self.errfile, 'w')
        else:
            efile = None
        (self.stdin, self.stdout, self.stderr) = (ifile, ofile, efile)
        shellval = not isinstance(self.cmd, tuple)
        logging.debug('Popen(%s, shell=%s, cwd=%s, stdin=%s, stdout=%s,'
                      'stderr=%s, bufsize=0, env=%s)', self.cmd,
                      shellval, self.wdir, ifile, ofile, efile, self.env)
        try:
            proc = Popen(self.cmd, shell=shellval, cwd=self.wdir,
                         stdin=ifile, stdout=ofile, stderr=efile,
                         bufsize=0, env=realenv)
        except (IOError, OSError):
            exc = exc_info()[1]
            if exc.args[0] == 2:  # ENOENT
                raise Error('ENOENT', 'Program not found')
            else:
                raise
        self.proc = proc
        if ifile == self.PIPE:
            self.stdin = proc.stdin
        if ofile == self.PIPE:
            self.stdout = proc.stdout
        if efile == self.PIPE:
            self.stderr = proc.stderr


class Timer(object):
    """Keep track of how long a section of code takes."""
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

    @staticmethod
    def now():
        """Return the current time."""
        from time import time
        return time()

    def start(self):
        """Start the timer."""
        if self.starttime is not None:
            raise RuntimeError('cannot start more than once without stopping')
        self.starttime = self.now()

    def stop(self):
        """Stop the timer and set the duration."""
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


class Verbose(object):
    # deprecated
    """Deprecated and should no longer be used."""
    def __init__(self, state=False, level=logging.INFO):
        self.level = level

    @staticmethod
    def _getlogger():
        """Return the default internal logger."""
        return logging.getLogger('pyerector.execute')

    @staticmethod
    def _getlevelnum(level):
        """Return the logging level based on its name."""
        return logging.getLevelName(level)

    def __bool__(self):
        return self._getlogger().isEnabledFor(self.level)

    def __call__(self, *args):
        warnings.warn("Use of Verbose is deprecated", DeprecationWarning)
        msg = ' '.join([str(s) for s in args])
        self._getlogger().log(self._getlevelnum(self.level), msg)


class LogFormatter(logging.Formatter, object):
    """Subclass to handle formatting messages from the library, including
prepending text in the PYERECTOR_PREFIX envvar and showing thread if not
the main threads (MainThread, PyErector)."""
    log_prefix = None

    def format(self, record):
        newrecord = super(LogFormatter, self).format(record)
        if self.log_prefix is None:
            try:
                prefix = os.environ['PYERECTOR_PREFIX']
            except (AttributeError, KeyError):
                prefix = ''
            self.log_prefix = prefix
        else:
            prefix = self.log_prefix
        if prefix:
            if isinstance(newrecord, logging.LogRecord):
                message = '%s: %s' % (prefix, newrecord.message)
            else:
                message = '%s: %s' % (prefix, newrecord)
        elif isinstance(newrecord, logging.LogRecord):
            message = newrecord.message
        else:
            message = newrecord
        from threading import currentThread
        if currentThread().name not in ('MainThread', 'PyErector'):
            name = currentThread().name
            ident = currentThread().ident
            if ident is None:
                message = '(%s) %s' % (name, message)
            else:
                message = '(%s[%x]) %s' % (name, ident, message)
        return message

    def formatException(self, exc_info):
        """Return similar to the default, but using exception.extract_tb
instead of traceback.extract_tb; the former adds the class being called.
"""
        from .exception import extract_tb
        etype, exception, tb = exc_info
        exc = traceback.format_exception_only(etype, exception)
        stack = traceback.format_list(extract_tb(tb))
        return ''.join(stack + exc)


class LogExecFormatter(LogFormatter):
    """Subclass of LogFormatter that shows the pyerector execution stack
instead of python's.
"""
    def formatException(self, exc_info):
        """Extract the pyerector execution stack and return a string with
that and the formatted exception.
"""
        stack = get_current_stack()
        etype, exception = exc_info[:2]
        lines = stack.extract() + \
                traceback.format_exception_only(etype, exception)
        return ''.join(lines).rstrip()


class InitLogging(Initialization):
    """Initialize the logging, creating two loggers, pyerector and
pyerector.execute."""
    deflevel = logging.WARNING
    message = '%(message)s'

    @staticmethod
    def setup(name, handlerklass, formatterklass,
              message=message):
        """Set up a new logger with appropriate settings."""
        fmtr = formatterklass(message)
        hndr = handlerklass()
        hndr.setFormatter(fmtr)
        lgr = logging.getLogger(name)
        lgr.addHandler(hndr)
        lgr.propagate = False
        return lgr

    def run(self):
        """Set the default logging level, create a 'DISPLAY' logging level,
create two loggers: pyerector and pyerector.execute, and if available,
set warnings to be captured by the logging module.
"""
        logging.basicConfig(level=self.deflevel, message=self.message)
        logging.addLevelName(level=logging.ERROR + 5, levelName='DISPLAY')
        self.setup('pyerector', logging.StreamHandler, LogFormatter)
        self.setup('pyerector.execute', logging.StreamHandler, LogExecFormatter)
        warnings.simplefilter("default", DeprecationWarning)
        if hasattr(logging, 'captureWarnings'):
            logging.captureWarnings(True)

InitLogging()

display = Verbose(None, 'DISPLAY')
warn = Verbose(None, 'ERROR')
verbose = Verbose(None, 'INFO')
debug = Verbose(None, 'DEBUG')

