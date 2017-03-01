#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.

import os
import sys
import unittest

try:
    from .base import *
except ValueError:
    sys.path.insert(
        0,
        os.path.normpath(
            os.path.join(
                os.path.dirname(__file__), os.pardir, os.pardir
            )
        )
    )
    from base import *

PyVersionCheck()

from pyerector.exception import Error
from pyerector.path import Path
from pyerector.helper import normjoin, Exclusions, Subcommand, newer, Timer

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
sys.stdout.write('%d\\n' % len(sys.stdin.read()))'''


class Testnormjoin(TestCase):
    def test_singlearg(self):
        self.assertEqual(normjoin('tmp'), 'tmp')

    def test_noarg(self):
        self.assertEqual(normjoin(), os.sep)

    def test_emptystr(self):
        self.assertEqual(normjoin(''), os.sep)

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


class Testnewer(TestCase):
    @classmethod
    def setUpClass(cls):
        import time
        super(Testnewer, cls).setUpClass()
        cls.file0 = cls.dir + 'file0'  # do not create
        cls.file1 = cls.dir + 'file1'
        cls.file2 = cls.dir + 'file2'
        cls.file3 = cls.dir + 'file3'
        cls.file1.open()
        cls.file2.open()
        cls.file3.open()
        now = time.time()
        cls.file1.utime(now, now)
        cls.file2.utime(now, now - 1000)
        cls.file3.utime(now, now - 3000)

    def test_nofiles(self):
        self.assertTrue(newer(self.file0, self.file0))
        self.assertTrue(newer(self.file0, self.file1))
        self.assertFalse(newer(self.file1, self.file0))

    def test_older(self):
        self.assertFalse(newer(self.file1, self.file2))
        self.assertFalse(newer(self.file2, self.file3))
        self.assertFalse(newer(self.file1, self.file3))
    def test_newer(self):
        self.assertTrue(newer(self.file2, self.file1))
        self.assertTrue(newer(self.file3, self.file2))
        self.assertTrue(newer(self.file3, self.file1))



class TestExclusions(TestCase):
    def setUp(self):
        from ..vcs import VCS
        self.defaults = Exclusions.defaults.copy()
        self.vcsdir = VCS().directory

    def test_init_(self):
        e = Exclusions(('src', 'bin'))
        self.assertSetEqual(e, set(('src', 'bin')))
        self.assertTrue(e.usedefaults)
        f = Exclusions(('back', 'there'), usedefaults=False)
        self.assertSetEqual(f, set(('back', 'there')))
        self.assertFalse(f.usedefaults)
        g = Exclusions(('up', 'here'), usedefaults=None)
        self.assertSetEqual(g, set(('up', 'here')))
        self.assertIsNone(g.usedefaults)
        h = Exclusions('str')
        self.assertSetEqual(h, set(('str',)))
        with self.assertRaises(TypeError):
            Exclusions(45)
            Exclusions({})
        f = Exclusions(e)
        self.assertSetEqual(f, set(('src', 'bin')))
        self.assertTrue(e.usedefaults)
        h = Exclusions(g)
        self.assertIsNone(h.usedefaults)

    def test_no_items(self):
        e = Exclusions()
        self.assertSetEqual(e.defaults, self.defaults)
        self.assertSetEqual(e, set())

    def test_nodefaults(self):
        e = Exclusions(usedefaults=False)
        self.assertSetEqual(e, set())
        self.assertFalse(e.match(Path('testhelper.py')))
        if self.vcsdir is not None:
            self.assertTrue(e.match(self.vcsdir))

    def test_items(self):
        e = Exclusions(('1', '2', '3'))
        self.assertSetEqual(e, set(('1', '2', '3')))
        self.assertTrue(e.match(Path('1')))
        self.assertTrue(e.match(Path('testhelper.pyc')))
        if self.vcsdir is not None:
            self.assertTrue(e.match(self.vcsdir))

    def test_items_no_defaults(self):
        e = Exclusions(('1', '2', '3'), usedefaults=False)
        self.assertSetEqual(e, set(('1', '2', '3')))
        self.assertTrue(e.match(Path('1')))
        self.assertFalse(e.match(Path('testhelper.pyc')))
        if self.vcsdir is not None:
            self.assertTrue(e.match(self.vcsdir))

    def test_items_none_defaults(self):
        e = Exclusions(('1', '2', '3'), usedefaults=None)
        self.assertSetEqual(e, set(('1', '2', '3')))
        self.assertTrue(e.match(Path('1')))
        self.assertFalse(e.match(Path('testhelper.pyc')))
        if self.vcsdir is not None:
            self.assertFalse(e.match(self.vcsdir))

    def test_match(self):
        e = Exclusions()
        self.assertTrue(e.match(Path('testhelper.pyc')))
        self.assertFalse(e.match(Path('testhelper.py')))

    def test_setdefaults(self):
        e = Exclusions()
        self.assertFalse(hasattr(Exclusions, 'real_defaults'))
        # call reset without setting the defaults first
        e.set_defaults(reset=True)
        self.assertFalse(hasattr(Exclusions, 'real_defaults'))
        e.set_defaults((Path('1'), Path('2'), Path('3')))
        self.assertSetEqual(e, set())
        self.assertTrue(hasattr(Exclusions, 'real_defaults'))
        self.assertTrue(e.match(Path('1')))
        self.assertFalse(e.match(Path('4')))
        f = Exclusions()
        self.assertTrue(f.match(Path('1')))
        self.assertFalse(e.match(Path('4')))
        self.assertSetEqual(f, set())
        f.set_defaults(reset=True)
        self.assertSetEqual(e, set())
        self.assertFalse(hasattr(Exclusions, 'real_defaults'))
        self.assertFalse(e.match(Path('1')))
        self.assertFalse(e.match(Path('4')))
        with self.assertRaises(TypeError):
            f.set_defaults(items='badtype')


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

    def test_subsequence(self):
        proc = Subcommand(
            ((sys.executable, '-c', Commands.succeed),),
        )
        self.assertEqual(proc.cmd, (sys.executable, '-c', Commands.succeed))
        proc.close()

    def test_wrongcmd(self):
        self.assertRaises(AssertionError, Subcommand, 'hithere')

    def test_wdir(self):
        import tempfile
        tmpdir = tempfile.gettempdir()
        fname = tempfile.mktemp()
        self.assertFalse(os.path.exists(fname))
        proc = None
        try:
            proc = Subcommand(
                (sys.executable, '-c', Commands.touch, os.path.basename(fname)),
                wdir=tmpdir
            )
            self.assertEqual(proc.returncode, 0)
            self.assertTrue(os.path.exists(fname))
        finally:
            if proc is not None:
                proc.close()
            if os.path.exists(fname):
                os.remove(fname)

    def test_stdin(self):
        infile = self.dir + 'stdin.stdin.txt'
        infile.open('wt').write('Spam, Spam, Spam, Spam!\nWonderful spam, beautiful spam!\n')
        proc = Subcommand(
            (sys.executable, '-c', Commands.wc),
            stdin=str(infile), stdout=Subcommand.PIPE
        )
        try:
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(proc.stdout.read().decode('UTF-8').rstrip(), '56')
        finally:
            proc.close()
        inf = infile.open('rt')
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
        proc = Subcommand(
            (sys.executable, '-c', Commands.succeed),
            stdin=Subcommand.PIPE, stdout=Subcommand.PIPE
        )
        try:
            self.assertEqual(proc.stdin, proc.proc.stdin)
        finally:
            proc.close()

    def test_stdout(self):
        contents = 'abcdefghijklmnopqrstuvwxyz0123456789\n'
        infile = self.dir + 'stdout.infile.txt'
        infile.open('wt').write(contents)
        outfile = self.dir + 'stdout.stdout.txt'
        proc = Subcommand(
            (sys.executable, '-c', Commands.cat, str(infile)),
            stdout=str(outfile)
        )
        try:
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(outfile.open('rt').read(), contents)
        finally:
            proc.close()
        outf = outfile.open('wt+')
        try:
            proc = Subcommand(
                (sys.executable, '-c', Commands.cat, str(infile)),
                stdout=outf
            )
            self.assertEqual(proc.returncode, 0)
            self.assertIs(proc.stdout, outf)
            outf.seek(0)
            self.assertEqual(outfile.open('rt').read(), contents)
        finally:
            outf.close()
            proc.close()

    def test_stderr(self):
        errfile = self.dir + 'stderr.stderr.txt'
        nonfile = self.dir + 'stderr.does-not-exist'
        proc = Subcommand(
            (sys.executable, '-c', Commands.cat, nonfile),
            stderr=str(errfile)
        )
        errmsg = 'no such file or directory\n'
        try:
            self.assertGreater(proc.returncode, 0)
            self.assertEqual(errfile.open().read(), errmsg)
        finally:
            proc.close()
        errf = errfile.open('wt+')
        try:
            proc = Subcommand(
                (sys.executable, '-c', Commands.cat, str(nonfile)),
                stderr=errf
            )
            self.assertGreater(proc.returncode, 0)
            self.assertIs(proc.stderr, errf)
            errf.seek(0)
            self.assertEqual(errf.read(), errmsg)
        finally:
            errf.close()
            proc.close()
        proc = Subcommand(
            (sys.executable, '-c', Commands.succeed),
            stderr=Subcommand.PIPE)
        try:
            self.assertEqual(proc.stderr, proc.proc.stderr)
        finally:
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
        finally:
            proc.close()
        del proc
        try:
            self.assertRaises(OSError, os.kill, pid, 0)
        except AssertionError:
            #os.system('ps uwp %d' % pid)
            raise

    def test_close(self):
        touchfile = self.dir + 'close.touch.txt'
        infile = self.dir + 'close.stdin.txt'
        outfile = self.dir + 'close.stdout.txt'
        errfile = self.dir + 'close.stderr.txt'
        infile.open('wt')  # just create the file
        proc = Subcommand(
            (sys.executable, '-c', Commands.touch, str(touchfile)),
            stdin=str(infile), stdout=str(outfile), stderr=str(errfile),
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

    def test_exceptions(self):
        with self.assertRaises(Error):
            Subcommand(('/bin/programdoesnotexist',))


class TestTimer(TestCase):
    def test_init_(self):
        t = Timer()
        self.assertIsNone(t.starttime)
        self.assertIsNone(t.duration)

    def testnow(self):
        import time
        now, rightnow = Timer.now(), time.time()
        self.assertEqual(round(now, 2), round(rightnow, 2))

    def teststart(self):
        t = Timer()
        t.start()
        self.assertIsInstance(t.starttime, float)
        with self.assertRaises(RuntimeError):
            t.start()

    def teststop(self):
        t = Timer()
        with self.assertRaises(RuntimeError):
            t.stop()
        t.start()
        t.stop()
        self.assertIsInstance(t.duration, float)
        self.assertIsNone(t.starttime)

    def test_context(self):
        """Use of a timer as a context manager to handle start/stop implicitly."""
        t = Timer()
        self.assertIsNone(t.starttime)
        self.assertIsNone(t.duration)
        with t:
            self.assertIsInstance(t.starttime, float)
            self.assertIsNone(t.duration)
        self.assertIsNone(t.starttime)
        self.assertIsInstance(t.duration, float)

    def test_repr_(self):
        t = Timer()
        self.assertEqual(repr(t), '<Timer unstarted>')
        t.starttime = 6.0
        self.assertEqual(repr(t), '<Timer started>')
        t.starttime = None
        t.duration = 5.0
        self.assertEqual(repr(t), '<Timer duration: 5.000>')

    def test_float_(self):
        t = Timer()
        self.assertEqual(float(t), 0.0)
        t.duration = 5.25
        self.assertEqual(float(t), 5.25)

    def test_int_(self):
        t = Timer()
        self.assertEqual(int(t), 0)
        t.duration = 5.25
        self.assertEqual(int(t), 5)

