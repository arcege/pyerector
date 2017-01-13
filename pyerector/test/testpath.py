#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly All rights reserved.

import os
import warnings

try:
    from .base import *
except ValueError:
    import sys
    sys.path.insert(
        0,
        os.path.normpath(
            os.path.join(
                os.path.dirname(__file__), os.pardir, os.pardir
            )
        )
    )
    from pyerector.test.base import *

PyVersionCheck()

from pyerector.variables import V
from pyerector.path import Path, homedir, rootdir

class Testhomedir(TestCase):
    def test_equal(self):
        self.assertEqual(str(homedir), os.environ['HOME'])

class Testrootdir(TestCase):
    def _test_equal(self):
        self.assertEqual(rootdir.value, os.sep)

class TestPath(TestCase):
    def setUp(self):
        import tempfile
        self.tdir = tempfile.mkdtemp()
        self.tpath = Path(self.tdir)
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tdir)

    def test_variables(self):
        from ..variables import V
        v = V('path_variables_a', 'foo')
        p = Path('xyzzy', v, 'README')
        self.assertEqual(p.value, 'xyzzy/foo/README')
        v.value = 'bar'
        self.assertEqual(p.value, 'xyzzy/bar/README')

    def test__init__(self):
        f = Path()
        self.assertFalse(f.has_variable)
        f = Path(V('basedir'))
        self.assertTrue(f.has_variable)
        f = Path('.', '/etc')
        self.assertEqual(f.components, ['', 'etc'])
        self.assertRaises(AttributeError, Path, [])

    def test_components(self):
        self.assertEqual(Path().components, [os.curdir])
        self.assertEqual(Path('.').components, ['.'])
        self.assertEqual(Path('/etc').components, ['', 'etc'])
        self.assertEqual(Path('/').components, ['', ''])

    def test_normalize(self):
        self.assertEqual(Path._normalize([]), [])
        self.assertEqual(Path._normalize(['']), ['', ''])
        self.assertEqual(Path._normalize([os.curdir]), [])
        self.assertEqual(Path._normalize(['', '']), ['', ''])
        self.assertEqual(Path._normalize([os.pardir]), [os.pardir])
        self.assertEqual(Path._normalize(['a', os.curdir, 'b']), ['a', 'b'])
        self.assertEqual(Path._normalize(['a', 'b', os.pardir]), ['a'])
        self.assertEqual(Path._normalize([V('basedir')]), [V('basedir')])
        self.assertEqual(Path._normalize(['', 'etc', os.pardir]), ['', ''])
        self.assertRaises(Exception, Path._normalize)

    def test__join(self):
        self.assertEqual(Path()._join(), '.')
        self.assertEqual(Path('/etc')._join(), '/etc')
        self.assertEqual(Path('/etc/..')._join(), '/')
        self.assertEqual(Path(V('foo', 'hi'))._join(), 'hi')
        self.assertEqual(Path('etc', Path('build'))._join(), 'etc/build')

    def test_value(self):
        p = Path()
        self.assertEqual(p.value, os.curdir)
        self.assertIsNotNone(p.stat)

    def test_basename(self):
        self.assertEqual(Path().basename, os.curdir)
        self.assertEqual(Path('/etc').basename, 'etc')
        self.assertEqual(Path('etc').basename, 'etc')

    def test_ext(self):
        self.assertEqual(Path().ext, '')
        self.assertEqual(Path('etc').ext, '')
        self.assertEqual(Path('hello.c').ext, '.c')

    def test_type(self):
        import socket
        os.mkdir(os.path.join(self.tdir, 'type.d'))
        open(os.path.join(self.tdir, 'type.f'), 'w')
        os.symlink('type.f', os.path.join(self.tdir, 'type.l'))
        os.mknod(os.path.join(self.tdir, 'type.p'), os.path.stat.S_IFIFO | 0777)
        s = socket.socket(socket.AF_UNIX)
        s.bind(os.path.join(self.tdir, 'type.o'))
        self.assertEqual(Path(self.tpath, 'type.n').type, Path.TYPE.NOENT)
        self.assertEqual(Path(self.tpath, 'type.d').type, Path.TYPE.DIR)
        self.assertEqual(Path(self.tpath, 'type.l').type, Path.TYPE.LINK)
        self.assertEqual(Path(self.tpath, 'type.f').type, Path.TYPE.FILE)
        self.assertEqual(Path(self.tpath, 'type.p').type, Path.TYPE.PIPE)
        self.assertEqual(Path(self.tpath, 'type.o').type, Path.TYPE.OTHER)

    def test_mtime(self):
        import time
        now = int(time.time())
        p = Path(self.tpath, 'mtime.f')
        self.assertIsNone(p.mtime)
        p.open('w')
        os.utime(str(p), (now, now))
        self.assertEqual(p.mtime, now)

    def test_atime(self):
        import time
        p = Path(self.tpath, 'atime.f')
        p.open('w')
        now = int(time.time())
        os.utime(str(p), (now, now))
        self.assertEqual(p.atime, now)
        self.assertEqual(p.atime, now)

    def test_ctime(self):
        import time
        p = Path(self.tpath, 'ctime.f')
        p.open('w')
        now = int(time.time())
        os.utime(str(p), (now, now))
        self.assertEqual(p.ctime, now)

    def test_abs(self):
        self.assertEqual(Path('etc').abs, os.path.join(os.getcwd(), 'etc'))

    def test_real(self):
        f = Path(self.tpath, 'real.f')
        l = Path(self.tpath, 'real.l')
        f.open('w')
        l.makelink('real.f')
        self.assertEqual(l.real, f.real)

    def test__len_(self):
        f = Path(self.tpath, 'len.f')
        d = Path(self.tpath, 'len.d')
        f.open('w').write('=' * 256)
        self.assertEqual(len(f), 256)
        d.mkdir()
        for i in range(2):
            Path(d, str(i)).open('w')
        self.assertEqual(len(d), 2)

    def test__iter_(self):
        d = Path(self.tpath, 'iter.d')
        d.mkdir()
        for i in range(2):
            Path(d, str(i)).open('w')
        i = 0
        for f in d:
            self.assertEqual(f.value, Path(d, str(i)).value)
            i += 1
        self.assertRaises(TypeError, iter(f))

    def test__hash_(self):
        f = Path('etc')
        self.assertEqual(hash(f), hash('etc'))

    def test__eq_(self):
        f1 = Path('etc')
        f2 = Path('etc')
        f3 = Path('etcetera')
        self.assertTrue(f1 == 'etc')
        self.assertTrue(f1 == f2)
        self.assertTrue('etc' == f1)
        self.assertFalse(f1 == f3)
        self.assertFalse(f1 == 'foobar')
        self.assertFalse('foobar' == f1)

    def test__lt_(self):
        f1 = Path('etc')
        f2 = Path('len')
        self.assertTrue(f1 < f2)
        self.assertTrue(f1 < 'len')
        self.assertFalse(f1 == f2)
        self.assertFalse(f1 > 'len')

    def test__add_(self):
        f1 = Path('etc')
        f2 = Path('etc')
        f3 = Path('etc', 'etc')
        self.assertEqual(f1 + f2, f3)
        self.assertEqual(f1 + 'etc', f3)
        self.assertEqual('etc' + f1, f3)

    def test__sub_(self):
        f1 = Path('etc', 'etc')
        f2 = Path('etc')
        f3 = Path('etc', 'len')
        self.assertEqual(f1 - f2, f2)
        self.assertEqual(f3 - f2, 'len')
        self.assertEqual(f2 - f1, os.pardir)

    def test_addext(self):
        self.assertEqual(Path('file').addext('.txt'), 'file.txt')

    def test_delext(self):
        self.assertEqual(Path('file.txt').delext(), 'file')

    def test_open(self):
        f1 = Path(self.tpath, 'open.f')
        self.assertRaises(TypeError, f1.open, 'r')
        f = f1.open()
        self.assertIsInstance(f, file)
        self.assertTrue(f1.isfile)
        self.assertEqual(f.mode, 'w')
        f.close()
        f = f1.open()
        self.assertIsInstance(f, file)
        self.assertEqual(f.mode, 'r')
        f.close()
        os.remove(f1.value)
        os.mkdir(f1.value)
        self.assertRaises(TypeError, f1.open, 'w')

    def test_match(self):
        f1 = Path('etc')
        self.assertTrue(f1.match('etc'))
        self.assertTrue(f1.match('et?'))
        self.assertTrue(f1.match('*'))
        self.assertFalse(f1.match('ETC'))
        #self.assertTrue(Path('ETC').match('etc', ignorecase=True))
        self.assertTrue(Path('foo', 'bar').match('bar'))
        self.assertFalse(Path('foo', 'bar').match('foo'))

    def test_glob(self):
        d = Path(self.tpath, 'glob.d')
        d.mkdir()
        for i in range(3):
            (d + str(i)).open()
        self.assertEqual([f.basename for f in sorted(d.glob('[0-9]'))], ['0', '1', '2'])

    def test_chmod(self):
        f = Path(self.tpath, 'chmod.f')
        self.assertFalse(f.exists)
        self.assertIsNone(f.chmod(0777))  # when file doesn't exist
        f.open()
        self.assertTrue(f.exists)
        self.assertIsNone(f.chmod(0777))
        self.assertEqual(f.mode, 0777)

    def test_remove(self):
        f = Path(self.tpath, 'remove.f')
        d = Path(self.tpath, 'remove.d')
        n = Path(self.tpath, 'remove.n')
        f.open()
        d.mkdir()
        self.assertIsNone(f.remove())
        self.assertFalse(f.exists)
        self.assertIsNone(d.remove())
        self.assertFalse(d.exists)
        self.assertIsNone(n.remove())
        self.assertFalse(n.exists)

    def test_rename(self):
        n = Path(self.tpath, 'rename.n')
        f = Path(self.tpath, 'rename.f')
        o = Path(self.tpath, 'rename.o')
        so = os.path.join(self.tdir, 'rename.so')  # string based
        self.assertRaises(TypeError, n.rename, 'rename.other')
        f.open()
        self.assertTrue(f.exists)
        other = f.rename(o)
        self.assertFalse(f.exists)
        self.assertTrue(other.exists)
        self.assertIs(o, other)
        other = o.rename(so)
        self.assertIsInstance(other, Path)
        self.assertFalse(o.exists)
        self.assertTrue(other.exists)
        self.assertEqual(other, so)

    def test_utime(self):
        import time
        f = Path(self.tpath, 'utime.f')
        f.open()
        when = time.time() - 3600
        self.assertTrue(f.isfile)
        f.utime(when, when - 3600)
        self.assertEqual(int(os.path.getatime(f.value)), int(when))
        self.assertEqual(int(os.path.getmtime(f.value)), int(when) - 3600)

    def test_copy(self):
        data = '=' * 256
        n = Path(self.tpath, 'copy.0')
        f = Path(self.tpath, 'copy.1')
        o = Path(self.tpath, 'copy.2')
        f.open().write(data)
        self.assertEqual(len(f), 256)
        f.copy(o)
        self.assertTrue(o.isfile)
        self.assertEqual(len(o), 256)
        self.assertEqual(o.open().read(), data)
        self.assertRaises(IOError, n.copy, o)

    def test_cwd(self):
        scd = os.path.abspath(os.curdir)
        sd = os.getcwd()
        srd = os.path.abspath(sd)
        here = Path.cwd()
        self.assertIsInstance(here, Path)
        self.assertEqual(scd, srd)
        self.assertEqual(here.value, scd)
        self.assertEqual(Path('foo').cwd().value, scd)

    def test_chdir(self):
        cwd = Path.cwd()
        try:
            self.assertIsNone(self.tpath.chdir())
            self.assertEqual(os.getcwd(), self.tdir)
            self.assertRaises((IOError, OSError), Path('chdir.n').chdir) # dir that doesn't exist
        finally:
            cwd.chdir()

    def test_mkdir(self):
        n = Path(self.tpath, 'mkdir.n')  # does not exist
        f = Path(self.tpath, 'mkdir.f')  # existing file
        d = Path(self.tpath, 'mkdir.d')  # existing directory
        d1 = d + 'subdir'
        d2 = d1 + 'subsubdir'
        f.open()
        os.mkdir(d.value)  # do it the old fashioned way for now
        self.assertTrue(f.isfile)
        self.assertRaises(TypeError, f.mkdir)
        self.assertIsNone(n.mkdir())
        self.assertTrue(n.isdir)
        self.assertTrue(d.isdir)
        self.assertIsNone(d.mkdir())
        self.assertFalse(d2.exists)
        self.assertIsNone(d2.mkdir())
        self.assertTrue(d2.isdir)
        self.assertTrue(d1.isdir)

    def test_readlink(self):
        n = Path(self.tpath, 'readlink.n')  # does not exist
        l = Path(self.tpath, 'readlink.l')  # existing link
        f = Path(self.tpath, 'readlink.f')  # existing file
        f.open()
        os.symlink(f.value, l.value)
        self.assertEqual(l.readlink(), f)
        self.assertRaises(TypeError, n.readlink)
        self.assertRaises(TypeError, f.readlink)

    def test_makelink(self):
        n = Path(self.tpath, 'makelink.n')  # does not exist
        l = Path(self.tpath, 'makelink.l')  # existing link
        f = Path(self.tpath, 'makelink.f')  # existing file
        d = Path(self.tpath, 'makelink.d')  # existing directory
        ptr = 'foobar'
        pptr = Path(ptr)
        self.assertIsNone(n.makelink(ptr))  # passing str value
        self.assertTrue(n.islink)
        self.assertEqual(os.readlink(n.value), ptr)
        n.remove()
        self.assertIsNone(n.makelink(pptr)) # passing Path instance
        self.assertTrue(n.islink)
        self.assertEqual(os.readlink(n.value), ptr)
        f.open()
        d.mkdir()
        os.symlink('xyzzy', l.value)
        self.assertRaises(TypeError, f.makelink, ptr)
        self.assertRaises(TypeError, d.makelink, ptr)
        self.assertIsNone(l.makelink(ptr))
        self.assertTrue(l.islink)
        self.assertEqual(os.readlink(l.value), ptr)

    def test_makepipe(self):
        mask = os.umask(0)
        try:
            n = Path(self.tpath, 'makepipe.n')  # does not exist
            f = Path(self.tpath, 'makepipe.f')  # existing file
            readonly = int('0666', 8)
            readwrite = int('0777', 8)
            f.open()
            self.assertRaises(TypeError, f.makepipe)
            self.assertIsNone(n.makepipe())
            self.assertEqual(n.type, Path.TYPE.PIPE)
            self.assertEqual(n.mode, readonly)
            n.remove()
            self.assertIsNone(n.makepipe(readwrite))
            self.assertEqual(n.type, Path.TYPE.PIPE)
            self.assertEqual(n.mode, readwrite)
        finally:
            os.umask(mask)


if __name__ == '__main__':
    import logging, unittest
    logging.getLogger('pyerector').level = logging.ERROR
    unittest.main()
