#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.

try:
    from .base import *
except ValueError:
    import os, sys
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

from pyerector.args import Arguments, ArgumentSet

class TestArguments(TestCase):
    def test_init_(self):
        h = Arguments()
        self.assertIsNone(h.list)
        self.assertEqual(h.map, {})
        with self.assertRaises(TypeError):
            Arguments('hi')  # must be an Arguments.Type instance
            Arguments(Arguments.List('foo'), Arguments.List('bar'))
            Arguments(Arguments.Keyword('foo'), Arguments.Keyword('foo')) # same name
        al1 = Arguments.List('xyzzy')
        ak1 = Arguments.Keyword('foo')
        ak2 = Arguments.Keyword('bar')
        h = Arguments(al1)
        self.assertEqual(h.list, al1)
        self.assertEqual(h.map, {'xyzzy': al1})
        h = Arguments(ak1, ak2)
        self.assertIsNone(h.list)
        self.assertEqual(h.map, {'foo': ak1, 'bar': ak2})

    def test__add_(self):
        al1 = Arguments.List('xyzzy')
        al2 = Arguments.List('ni!')
        ak1 = Arguments.Keyword('foo')
        ak2 = Arguments.Keyword('bar')
        #  no arguments left or right
        h = Arguments() + Arguments()
        self.assertIsNone(h.list)
        self.assertEqual(h.map, {})
        # same list, both left and right
        h = Arguments(al1) + Arguments(al1)
        self.assertEqual(h.list, al1)
        self.assertEqual(h.map, {al1.name: al1})
        # self has list, right has keyword
        h = Arguments(al1) + Arguments(ak1)
        self.assertEqual(h.list, al1)
        self.assertEqual(h.map, {al1.name: al1, ak1.name: ak1})
        # left has list, right has different list
        h = Arguments(al1) + Arguments(al2)
        self.assertEqual(h.list, al1)
        self.assertEqual(h.map, {al1.name: al1})
        # left has keyword, right has different keyword
        h = Arguments(ak1) + Arguments(ak2)
        self.assertEqual(h.map, {ak1.name: ak1, ak2.name: ak2})
        # left has keyword, right has same keyword
        h = Arguments(ak1) + Arguments(ak1)
        self.assertEqual(h.map, {ak1.name: ak1})
        # right has list and keyword, right has different keyword
        h = Arguments(al1, ak1) + Arguments(ak2)
        self.assertEqual(h.list, al1)
        self.assertEqual(h.map, {al1.name: al1, ak1.name: ak1, ak2.name: ak2})

    def testprocess(self):
        h = Arguments()
        a = h.process((), {})
        self.assertIsInstance(a, ArgumentSet)
        self.assertItemsEqual(a.list, ())
        self.assertItemsEqual(a.map, {})
        with self.assertRaises(ValueError):
            h.process(('foo',), {})  # not expecting positional arguments
            h.process((), {'foo': 'a'})  # not a valid keyword
        h = Arguments(
            Arguments.List('xyzzy'),
            Arguments.Keyword('foo', types=int, default=5),
            Arguments.Keyword('bar', types=tuple, default=()),
            Arguments.Keyword('ni'),
        )
        a = h.process((), {})
        self.assertItemsEqual(a.list, ())
        self.assertItemsEqual(a.map, {'ni': None, 'foo': 5, 'bar': (), 'xyzzy': ()})
        a1 = h.process(('foo',), {})
        self.assertNotEqual(a, a1)
        self.assertItemsEqual(a1.list, ('foo',))
        self.assertItemsEqual(a1.map, {'ni': None, 'foo': 5, 'bar': (), 'xyzzy': ('foo',)})
        del a1
        with self.assertRaises(TypeError):
            h.process((5,), {})
            h.process((), {'ni': 5})
            h.process((), {'bar': 'far'})
        a = h.process(('a', '', 'c'), {'bar': ('8', 9, '10')})
        self.assertItemsEqual(a.list, ('a', '', 'c'))
        self.assertItemsEqual(a.map['bar'], ('8', 9, '10'))
        b = h.process(('d', 'e'), {'ni': 'arcege'}, existing=a)
        self.assertItemsEqual(b.list, ('d', 'e'))
        self.assertItemsEqual(b.map, {'ni': 'arcege', 'bar': ('8', '9', '10'), 'foo': 5, 'xyzzy': ('d', 'e')})

class TestArguments_Type(TestCase):
    def test_init_(self):
        t = Arguments.Type('foobar')
        self.assertEqual(t.name, 'foobar')
        self.assertEqual(t.types, str)
        self.assertEqual(t.typenames, 'str')
        self.assertEqual(t.cast, str)
        t = Arguments.Type('', types=int)
        self.assertEqual(t.types, int)
        self.assertEqual(t.typenames, 'int')
        self.assertEqual(t.cast, int)
        t = Arguments.Type('', types=(str, int))
        self.assertEqual(t.types, (str, int))
        self.assertEqual(t.typenames, 'str, int')
        with self.assertRaises(TypeError):
            Arguments.Type('', types='str')  # must pass type or sequence of types
            Arguments.Type('', types=(str, 'int'))
            Arguments.Type('', cast='str')
        with self.assertRaises(ValueError):
            Arguments.Type('', cast=int)  # must be one of types
        t = Arguments.Type('', types=(float, int, str))  # implicit casting as float
        self.assertEqual(t.cast, float)
        t = Arguments.Type('', types=(int, float, str), cast=float)
        self.assertEqual(t.cast, float)

    def testprocess_value(self):
        t = Arguments.Type('foobar')
        self.assertEqual(t.process('foobar'), 'foobar')

    def testcheck_type(self):
        t = Arguments.Type('')
        self.assertIsNone(t.check_type('foo'))   # pass a str, no exception
        self.assertRaises(TypeError, t.check_type, (5,))

    def testprocess(self):
        t = Arguments.Type('')
        self.assertEqual(t.process('foobar'), 'foobar')
        self.assertRaises(TypeError, t.process, (5,))

class TestArgumentsList(TestCase):
    def testcheck_type(self):
        t = Arguments.List('foobar')
        self.assertEqual(t.name, 'foobar')
        self.assertEqual(t.types, str)
        self.assertIsNone(t.check_type(('str', 'bar')))
        self.assertRaises(AssertionError, t.check_type, None)
        self.assertRaises(TypeError, t.check_type, ('str', 5))
        t = Arguments.List('foobar', types=int)
        self.assertIsNone(t.check_type((0, 1, 2)))
        self.assertRaises(TypeError, t.check_type, ('str', 5))

class TestArgumentsKeyword(TestCase):
    def test_init_(self):
        k = Arguments.Keyword('name')
        self.assertEqual(k.name, 'name')
        self.assertEqual(k.types, str)
        self.assertIsNone(k.default)
        self.assertFalse(k.noNone)
        k = Arguments.Keyword('name', types=int, default=5, noNone=True)
        self.assertEqual(k.name, 'name')
        self.assertEqual(k.types, int)
        self.assertEqual(k.default, 5)
        self.assertTrue(k.noNone)
        self.assertRaises(TypeError, Arguments.Keyword, ('name',), {'types': int, 'defaults': 'str'})

    def testcheck_type(self):
        k = Arguments.Keyword('name')
        self.assertIsNone(k.check_type('a'))
        self.assertIsNone(k.check_type(None))
        self.assertRaises(TypeError, k.check_type, (5,))
        k = Arguments.Keyword('name', default='foo')
        self.assertIsNone(k.check_type(None))

    def testprocess_value(self):
        k = Arguments.Keyword('name')
        self.assertEqual(k.process_value('foo'), 'foo')
        self.assertEqual(k.process_value(None), None)
        k = Arguments.Keyword('name', noNone=True)
        with self.assertRaises(ValueError):
            k.process_value(None)
        k = Arguments.Keyword('name', default='foo')
        self.assertEqual(k.process_value(None), 'foo')

class TestArgumentSet(TestCase):
    def test_init_(self):
        t, k = (), {}
        a = ArgumentSet(t, k)
        self.assertIs(a.list, t)
        self.assertIs(a.map, k)
        with self.assertRaises(AssertionError):
            ArgumentSet([], {})  # must pass tuple
            ArgumentSet((), [])  # must pass dict

    def test_getattr_(self):
        a = ArgumentSet((), {'foo': 'bar'})
        self.assertEqual(getattr(a, 'foo'), 'bar')
        with self.assertRaises(AttributeError):
            a.bar

    def testitems(self):
        a = ArgumentSet((), {'foo': 'bar', 'xyzzy': 'ni'})
        self.assertItemsEqual(a.items(), [('foo', 'bar'), ('xyzzy', 'ni')])
    def testkeys(self):
        a = ArgumentSet((), {'foo': 'bar', 'xyzzy': 'ni'})
        self.assertEqual(a.keys(), ['foo', 'xyzzy'])
    def testvalues(self):
        a = ArgumentSet((), {'foo': 'bar', 'xyzzy': 'ni'})
        self.assertItemsEqual(a.values(), ['bar', 'ni'])
    def test_iter_(self):
        a = ArgumentSet((), {})
        self.assertIsInstance(iter(a), type(iter(())))
        self.assertItemsEqual(iter(a), ())
        a = ArgumentSet((1, 3, 4), {})
        self.assertItemsEqual(iter(a), (1, 3, 4))

    def test_len_(self):
        a = ArgumentSet((), {})
        self.assertEqual(len(a), 0)
        a = ArgumentSet((1, 2, 3), {})
        self.assertEqual(len(a), 3)

    def test_getitem_(self):
        a = ArgumentSet((), {})
        with self.assertRaises(IndexError):
            a[0]
        a = ArgumentSet((1, 2), {'a': 5, 'b': []})
        self.assertEqual(a[0], 1)
        self.assertEqual(a[1], 2)
        self.assertEqual(a['a'], 5)
        self.assertEqual(a['b'], [])
        with self.assertRaises(TypeError):
            a[5.4]

