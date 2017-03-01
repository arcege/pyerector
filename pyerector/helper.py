#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.
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

import logging
import os
from sys import exc_info
import traceback
import warnings

from .exception import Error
from .execute import get_current_stack, Initialization
from .path import Path

__all__ = [
    'Exclusions',
    'normjoin',
    'Subcommand',
    'newer',
]

# helper routines


def normjoin(*args):
    """Join and normalize the arguments into a pathname."""
    if not args:
        args = ('',)
    return Path(*args)


def newer(file1, file2, logger=None):
    """Return true if file2 is newer than file1.  Return True if
file1 does not exist, return False is file2 does not exist."""
    time1, time2 = Path(file1).mtime, Path(file2).mtime
    if logger:
        logger.debug('newer(%s, %s) => (%s, %s)', file1, file2, time1, time2)
    if time1 is None:
        return True
    elif time2 is None:
        return False
    else:
        return time1 <= time2


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
            # pylint: disable=no-member
            if usedefaults != items.usedefaults:
                # pylint: disable=no-member
                usedefaults = items.usedefaults
            items = set(items)
        elif not isinstance(items, (str, set, tuple, list, type(None))):
            raise TypeError('Exclusions: expecting str, set, tuple or list')
        if isinstance(items, str):  # proper casting
            # pylint: disable=redefined-variable-type
            items = (items,)
        if items:
            initialset = set(items)
        else:
            initialset = set()
        self.usedefaults = usedefaults
        super(Exclusions, self).__init__(initialset)

    def copy(self):
        return self.__class__(self)

    def match(self, string):
        """Return true if the given string matches one of the patterns
in the set."""
        # augment the possible matches with the defaults
        if self.usedefaults is None:
            matches = self
        elif self.usedefaults:
            matches = self | self.defaults
        else:
            matches = self | self.vcs_names
        values = [v for v in matches if Path(string).match(v)]
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


# pylint: disable=too-many-instance-attributes
class Subcommand(object):
    """Handles some of the subprocess details."""
    try:
        import subprocess
    except ImportError:
        subprocess = None
        raise NotImplementedError("Earlier than Python 2.6 is unsupported")
    PIPE = subprocess.PIPE

    # pylint: disable=too-many-arguments
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
        #import traceback
        logging.getLogger('pyerector.execute').debug(
            'starting %s.__del__()', self.__class__.__name__
        )
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

    def handle_pipe(self, afile, methodname, mode, alt=None):
        """Return a file object based on what type the file argument is."""
        if alt is not None and afile == alt:
            return alt
        elif hasattr(afile, methodname):  # file-line object
            return afile
        elif afile == self.PIPE:  # sentinal
            return self.PIPE
        elif isinstance(afile, Path):  # Path
            return afile.open(mode)
        elif hasattr(afile, 'lower'):  # str
            return open(str(afile), mode)
        else:
            return None

    def call_subprocess(self):
        """Call subprocess.Popen and handle the I/O."""
        from subprocess import Popen
        realenv = os.environ.copy()
        # convert env to strings
        env = dict([(n, str(self.env[n])) for n in self.env])
        realenv.update(env)
        ifile = self.handle_pipe(self.infile, 'read', 'r')
        ofile = self.handle_pipe(self.outfile, 'write', 'w')
        efile = self.handle_pipe(self.errfile, 'write', 'w', alt=self.outfile)
        (self.stdin, self.stdout, self.stderr) = (ifile, ofile, efile)
        shellval = not isinstance(self.cmd, tuple)
        cmd = tuple(str(c) for c in self.cmd)
        logging.getLogger('pyerector.execute').debug(
            'Popen(%s, shell=%s, cwd=%s, stdin=%s, stdout=%s,'
            'stderr=%s, bufsize=0, env=%s)', cmd,
            shellval, repr(self.wdir), ifile, ofile, efile, env
        )
        try:
            proc = Popen(cmd,
                         shell=shellval, cwd=str(self.wdir),
                         stdin=ifile, stdout=ofile, stderr=efile,
                         bufsize=0, env=realenv)
        except (IOError, OSError):
            exc = exc_info()[1]
            if exc.args[0] == 2:  # ENOENT
                raise Error('ENOENT', 'Program not found: %s' % self.cmd[0])
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


# pylint: disable=too-few-public-methods
class Verbose(object):
    """Deprecated and should no longer be used."""
    # deprecated
    # pylint: disable=unused-argument
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

    def formatException(self, exc_data):
        """Return similar to the default, but using exception.extract_tb
instead of traceback.extract_tb; the former adds the class being called.
"""
        from .exception import extract_tb
        etype, exception, etb = exc_data
        exc = traceback.format_exception_only(etype, exception)
        stack = traceback.format_list(extract_tb(etb))
        return ''.join(stack + exc)


class LogExecFormatter(LogFormatter):
    """Subclass of LogFormatter that shows the pyerector execution stack
instead of python's.
"""
    def formatException(self, exc_data):
        """Extract the pyerector execution stack and return a string with
that and the formatted exception.
"""
        stack = get_current_stack()
        etype, exception = exc_data[:2]
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
        logging.addLevelName(level=DISPLAY, levelName='DISPLAY')
        self.setup('pyerector', logging.StreamHandler, LogFormatter)
        self.setup('pyerector.execute', logging.StreamHandler, LogExecFormatter)
        warnings.simplefilter("default", DeprecationWarning)
        if hasattr(logging, 'captureWarnings'):
            logging.captureWarnings(True)

DISPLAY = logging.ERROR + 5
InitLogging()

# these are deprecated
# pylint: disable=invalid-name
display = Verbose(None, 'DISPLAY')
# pylint: disable=invalid-name
warn = Verbose(None, 'ERROR')
# pylint: disable=invalid-name
verbose = Verbose(None, 'INFO')
# pylint: disable=invalid-name
debug = Verbose(None, 'DEBUG')

