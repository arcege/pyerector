#!/usr/bin/python
# Copyright @ 2012-2015 Michael P. Reilly. All rights reserved.

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

from pyerector.helper import normjoin, Exclusions, Subcommand

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
        from ..vcs import VCS
        self.defaults = Exclusions.defaults.copy()
        self.vcsdir = VCS().directory

    def test_no_items(self):
        e = Exclusions()
        self.assertSetEqual(e.defaults, self.defaults)
        self.assertSetEqual(e, set())

    def test_nodefaults(self):
        e = Exclusions(usedefaults=False)
        self.assertSetEqual(e, set())
        self.assertFalse(e.match('testhelper.py'))
        if self.vcsdir is not None:
            self.assertTrue(e.match(self.vcsdir))

    def test_items(self):
        e = Exclusions(('1', '2', '3'))
        self.assertSetEqual(e, set(('1', '2', '3')))
        self.assertTrue(e.match('1'))
        self.assertTrue(e.match('testhelper.pyc'))
        if self.vcsdir is not None:
            self.assertTrue(e.match(self.vcsdir))

    def test_items_nodefaults(self):
        e = Exclusions(('1', '2', '3'), usedefaults=False)
        self.assertSetEqual(e, set(('1', '2', '3')))
        self.assertTrue(e.match('1'))
        self.assertFalse(e.match('testhelper.pyc'))
        if self.vcsdir is not None:
            self.assertTrue(e.match(self.vcsdir))

    def test_items_nonedefaults(self):
        e = Exclusions(('1', '2', '3'), usedefaults=None)
        self.assertSetEqual(e, set(('1', '2', '3')))
        self.assertTrue(e.match('1'))
        self.assertFalse(e.match('testhelper.pyc'))
        if self.vcsdir is not None:
            self.assertFalse(e.match(self.vcsdir))

    def test_match(self):
        e = Exclusions()
        self.assertTrue(e.match('testhelper.pyc'))
        self.assertFalse(e.match('testhelper.py'))

    def test_setdefaults(self):
        e = Exclusions()
        self.assertFalse(hasattr(Exclusions, 'real_defaults'))
        e.set_defaults(('1', '2', '3'))
        self.assertSetEqual(e, set())
        self.assertTrue(hasattr(Exclusions, 'real_defaults'))
        self.assertTrue(e.match('1'))
        self.assertFalse(e.match('4'))
        f = Exclusions()
        self.assertTrue(f.match('1'))
        self.assertFalse(e.match('4'))
        self.assertSetEqual(f, set())
        f.set_defaults(reset=True)
        self.assertSetEqual(e, set())
        self.assertFalse(hasattr(Exclusions, 'real_defaults'))
        self.assertFalse(e.match('1'))
        self.assertFalse(e.match('4'))


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
        finally:
            proc.close()
        del proc
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
        open(infile, 'wt')  # just create the file
        proc = Subcommand(
            (sys.executable, '-c', Commands.touch, touchfile),
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

if __name__ == '__main__':
    import logging, unittest
    logging.getLogger('pyerector').level = logging.ERROR
    unittest.main()
