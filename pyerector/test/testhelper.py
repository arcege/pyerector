#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import os
import sys
import unittest

from .base import *

PyVersionCheck()

from pyerector.helper import Verbose, normjoin, u, Exclusions, Subcommand
from pyerector import debug

try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO

class Commands:
    succeed = 'raise SystemExit(0)'
    fail = 'raise SystemExit(1)'
    sleep = '''import sys, time
time.sleep(float(sys.argv[1]))'''
    cat = '''import sys
try:
    if len(sys.argv) > 1:
        for filename in sys.argv[1:]:
            if filename == '-':
                sys.stdout.write(sys.stdin.read())
            else:
                sys.stdout.write(open(filename, 'rt').read())
    else:
        sys.stdout.write(sys.stdin.read())
except IOError:
    raise SystemExit('no such file or directory')'''
    touch = '''import sys
try:
    for filename in sys.argv[1:]:
        open(filename, 'wb')  # just create the file
except IOError:
    raise SystemExit('unable to create file')'''
    wc = '''import sys
print len(sys.stdin.read())'''

class StringIOVerbose(Verbose):
    def __init__(self, state=False):
        super(StringIOVerbose, self).__init__(state)
        self.stream = StringIO()

class TestVerbose(TestCase):
    def test_init(self):
        v = Verbose()
        self.assertIs(v.stream, sys.stdout)
        self.assertEqual(v.eoln, os.linesep)
        self.assertEqual(v.prefix, '')
    def test_init_False(self):
        v = Verbose(False)
        self.assertFalse(v.state)
    def test_init_True(self):
        v = Verbose(True)
        self.assertTrue(v.state)
    def test_init_nonboolean(self):
        v = Verbose(1)
        self.assertTrue(v.state)
        v = Verbose('')
        self.assertFalse(v.state)
        v = Verbose(None)
        self.assertFalse(v.state)
    def test_on(self):
        v = Verbose()
        self.assertFalse(v.state)
        v.on()
        self.assertTrue(v.state)
    def test_off(self):
        v = Verbose(True)
        self.assertTrue(v.state)
        v.off()
        self.assertFalse(v.state)
    def test_bool_(self):
        v = Verbose()
        self.assertFalse(bool(v))
        v = Verbose(True)
        self.assertTrue(bool(v))
    def test_write(self):
        v = StringIOVerbose()
        self.assertIsInstance(v.stream, StringIO)
        v.write('foobar')
        self.assertEqual(v.stream.getvalue(), u('foobar' + v.eoln))
    def test_call_off(self):
        v = StringIOVerbose()
        v.off()
        self.assertIsInstance(v.stream, StringIO)
        v('foobar')
        self.assertEqual(v.stream.getvalue(), u(''))
    def test_call_on(self):
        v = StringIOVerbose()
        v.on()
        self.assertIsInstance(v.stream, StringIO)
        v('foobar')
        self.assertEqual(v.stream.getvalue(), u('foobar' + v.eoln))
    def test_call_multiargs(self):
        v = StringIOVerbose()
        v.on()
        v('foo', 'bar')
        self.assertEqual(v.stream.getvalue(), u('foo bar' + v.eoln))
    def test_prefix(self):
        if 'PYERECTOR_PREFIX' in os.environ:
            backup_prefix = os.environ['PYERECTOR_PREFIX']
        else:
            backup_prefix = None
        os.environ['PYERECTOR_PREFIX'] = 'unittest-prefix'
        try:
            v = StringIOVerbose(True)
            self.assertEqual(v.prefix, 'unittest-prefix')
            v('foo', 'bar')
            self.assertEqual(v.stream.getvalue(),
                             u('unittest-prefix: foo bar' + v.eoln))
        finally:
            if backup_prefix:
                os.environ['PYERECTOR_PREFIX'] = backup_prefix
            else:
                del os.environ['PYERECTOR_PREFIX']

class Testnormjoin(TestCase):
    def test_singlearg(self):
        self.assertEqual(normjoin('tmp'), 'tmp')
    def test_noarg(self):
        self.assertEqual(normjoin(), os.curdir)
    def test_emptystr(self):
        self.assertEqual(normjoin(''), os.curdir)
    def test_pardir(self):
        self.assertEqual(
            normjoin('tmp', '..', 'etc'),
            'etc'
        )
    def test_curdir(self):
        self.assertEqual(
            normjoin('tmp', '.', 'etc'),
            os.path.join('tmp', 'etc')
        )

class TestExclusions(TestCase):
    def setUp(self):
        self.defaults = Exclusions.defaults.copy()
    def test_no_items(self):
        e = Exclusions()
        self.assertSetEqual(e.defaults, self.defaults)
        self.assertSetEqual(e, self.defaults)
    def test_nodefaults(self):
        e = Exclusions(usedefaults=False)
        self.assertSetEqual(e, set())
    def test_items(self):
        e = Exclusions((1, 2, 3))
        self.assertSetEqual(e, self.defaults | set((1,2,3)))
    def test_items_nodefaults(self):
        e = Exclusions((1, 2, 3), usedefaults=False)
        self.assertSetEqual(e, set((1,2,3)))
    def test_match(self):
        e = Exclusions()
        self.assertTrue(e.match('testhelper.pyc'))
        self.assertFalse(e.match('testhelper.py'))
    def test_setdefaults(self):
        e = Exclusions()
        self.assertFalse(hasattr(Exclusions, 'real_defaults'))
        e.set_defaults((1, 2, 3))
        self.assertTrue(hasattr(Exclusions, 'real_defaults'))
        self.assertSetEqual(e, self.defaults)
        f = Exclusions()
        self.assertSetEqual(f, set((1,2,3)))
        f.set_defaults(reset = True)
        self.assertSetEqual(e, self.defaults)
        self.assertFalse(hasattr(Exclusions, 'real_defaults'))

class TestSubcommand(TestCase):
    def test_simple(self):
        proc = Subcommand(  # should just return success
            (sys.executable, '-c', Commands.succeed),
        )
        self.assertEqual(proc.returncode, 0)
        proc.close()
        proc = Subcommand(  # should just return failure
            (sys.executable, '-c', Commands.fail),
        )
        self.assertEqual(proc.returncode, 1)
        proc.close()
    def test_wrongcmd(self):
        self.assertRaises(AssertionError, Subcommand, 'hithere')
    def test_wdir(self):
        import tempfile
        tmpdir = tempfile.gettempdir()
        fname = tempfile.mktemp()
        self.assertFalse(os.path.exists(fname))
        try:
            proc = Subcommand(
                (sys.executable, '-c', Commands.touch, os.path.basename(fname)),
                wdir=tmpdir
            )
            self.assertEqual(proc.returncode, 0)
            self.assertTrue(os.path.exists(fname))
        finally:
            proc.close()
            if os.path.exists(fname):
                os.remove(fname)
    def test_stdin(self):
        infile = os.path.join(self.dir, 'stdin.stdin.txt')
        open(infile, 'wt').write('Spam, Spam, Spam, Spam!\nWonderful spam, beautiful spam!\n')
        proc = Subcommand(
            (sys.executable, '-c', Commands.wc),
            stdin=infile, stdout=Subcommand.PIPE
        )
        try:
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(proc.stdout.read().decode('UTF-8').rstrip(), '56')
        finally:
            proc.close()
        inf = open(infile, 'rt')
        try:
            proc = Subcommand(
                (sys.executable, '-c', Commands.wc),
                stdin=inf, stdout=Subcommand.PIPE
            )
            self.assertEqual(proc.returncode, 0)
            self.assertIs(proc.stdin, inf)
            self.assertEqual(proc.stdout.read().decode('UTF-8').strip(), '56')
        finally:
            proc.close()
            inf.close()
    def test_stdout(self):
        contents = 'abcdefghijklmnopqrstuvwxyz0123456789\n'
        infile = os.path.join(self.dir, 'stdout.infile.txt')
        open(infile, 'wt').write(contents)
        outfile = os.path.join(self.dir, 'stdout.stdout.txt')
        proc = Subcommand(
            (sys.executable, '-c', Commands.cat, infile),
            stdout=outfile
        )
        try:
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(open(outfile, 'rt').read(), contents)
        finally:
            proc.close()
        outf = open(outfile, 'wt+')
        try:
            proc = Subcommand(
                (sys.executable, '-c', Commands.cat, infile),
                stdout=outf
            )
            self.assertEqual(proc.returncode, 0)
            self.assertIs(proc.stdout, outf)
            outf.seek(0)
            self.assertEqual(open(outfile, 'rt').read(), contents)
        finally:
            outf.close()
            proc.close()
    def test_stderr(self):
        errfile = os.path.join(self.dir, 'stderr.stderr.txt')
        nonfile = os.path.join(self.dir, 'stderr.does-not-exist')
        proc = Subcommand(
            (sys.executable, '-c', Commands.cat, nonfile),
            stderr=errfile
        )
        errmsg = 'no such file or directory\n'
        try:
            self.assertGreater(proc.returncode, 0)
            self.assertEqual(open(errfile, 'rt').read(), errmsg)
        finally:
            proc.close()
        errf = open(errfile, 'wt+')
        try:
            proc = Subcommand(
                (sys.executable, '-c', Commands.cat, nonfile),
                stderr=errf
            )
            self.assertGreater(proc.returncode, 0)
            self.assertIs(proc.stderr, errf)
            errf.seek(0)
            self.assertEqual(errf.read(), errmsg)
        finally:
            errf.close()
            proc.close()
    def test_signal(self):
        if self.platform == 'win':
            raise SkipTest('Broken OS')
        proc = Subcommand(
            (sys.executable, '-c', Commands.sleep, '10'),
            wait=False
        )
        try:
            proc.terminate()
            self.assertIsNone(proc.returncode, None)
            proc.wait()
            self.assertLess(proc.returncode, 0)
            self.assertEqual(proc.returncode, -15)
        finally:
            proc.close()
    def _test_PIPE(self):
        pass
    def _test_env(self):
        pass
    def test_nowait(self):
        from time import sleep
        proc = Subcommand(
            (sys.executable, '-c', Commands.sleep, '0.1'),
            wait=False
        )
        try:
            self.assertFalse(proc.poll())
            sleep(0.2)
            self.assertTrue(proc.poll())
            self.assertEqual(proc.returncode, 0)
        finally:
            proc.close()
        proc = Subcommand(
            (sys.executable, '-c', Commands.sleep, '0.1'),
            wait=False
        )
        try:
            self.assertFalse(proc.poll())
            rc = proc.wait()
            self.assertEqual(rc, proc.returncode)
            self.assertEqual(proc.returncode, 0)
        finally:
            proc.close()
    def test_terminate(self):
        if self.platform == 'win':
            raise SkipTest('Broken OS')
        proc = Subcommand(
            (sys.executable, '-c', Commands.sleep, '0.2'),
            wait=False
        )
        try:
            self.assertIsNone(os.kill(proc.proc.pid, 0))
            proc.terminate()
            rc = proc.wait()
            self.assertLess(rc, 0)
            self.assertEqual(rc, -15)
            self.assertRaises(OSError, os.kill, proc.proc.pid, 0)
        finally:
            proc.close()
    def test_kill(self):
        if self.platform == 'win':
            raise SkipTest('Broken OS')
        proc = Subcommand(
            (sys.executable, '-c', Commands.sleep, '0.2'),
            wait=False
        )
        try:
            self.assertIsNone(os.kill(proc.proc.pid, 0))
            proc.kill()
            rc = proc.wait()
            self.assertLess(rc, 0)
            self.assertEqual(rc, -9)
            self.assertRaises(OSError, os.kill, proc.proc.pid, 0)
        finally:
            proc.close()
    @unittest.skip('not calling __del__ properly here')
    def test_del_(self):
        proc = Subcommand(
            (sys.executable, '-c', Commands.sleep, '0.2'),
            wait=False
        )
        try:
            pid = proc.proc.pid
            self.assertIsNone(os.kill(pid, 0))
            debug.on()
        finally:
            proc.close()
        del proc
        debug.off()
        try:
            self.assertRaises(OSError, os.kill, pid, 0)
        except AssertionError:
            #os.system('ps uwp %d' % pid)
            raise
    def test_close(self):
        touchfile = os.path.join(self.dir, 'close.touch.txt')
        infile = os.path.join(self.dir, 'close.stdin.txt')
        outfile = os.path.join(self.dir, 'close.stdout.txt')
        errfile = os.path.join(self.dir, 'close.stderr.txt')
        open(infile, 'wt') # just create the file
        proc =  Subcommand(
            (sys.executable, '-c' , Commands.touch, touchfile),
            stdin=infile, stdout=outfile, stderr=errfile,
            wait=False,
        )
        self.assertFalse(proc.stdin.closed)
        self.assertFalse(proc.stdout.closed)
        self.assertFalse(proc.stderr.closed)
        proc.wait()
        self.assertTrue(proc.stdin.closed)
        self.assertFalse(proc.stdout.closed)
        self.assertFalse(proc.stderr.closed)
        proc.close()
        self.assertIsNone(proc.stdin)
        self.assertIsNone(proc.stdout)
        self.assertIsNone(proc.stderr)

