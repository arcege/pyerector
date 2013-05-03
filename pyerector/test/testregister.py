#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

from .base import PyVersionCheck, TestCase

PyVersionCheck()

from pyerector.register import Register, registry

class A:
    pass
class B:
    pass
class C(A):
    pass
class D(A, B):
    pass

class TestRegister(TestCase):
    def setUp(self):
        self.r = Register()
        self.r.append('A', A)
        self.r.append('B', B)
        self.r.append('C', C)
        self.r.append('D', D)
    def test_append(self):
        self.assertDictEqual(self.r.map, {'A': A, 'B': B, 'C': C, 'D': D})
    def test_contains_(self):
        self.assertTrue('A' in self.r)
        self.assertFalse('E' in self.r)
    def test_getitem_(self):
        self.assertEqual(self.r['A'], A)
        with self.assertRaises(KeyError):
            self.r['E']
    def test_setitem_(self):
        self.r['A'] = D
        self.assertEqual(self.r.map['A'], D)
    def test_delitem_(self):
        self.assertDictEqual(self.r.map, {'A': A, 'B': B, 'C': C, 'D': D})
        del self.r['B']
        self.assertDictEqual(self.r.map, {'A': A, 'C': C, 'D': D})
    def test_len_(self):
        self.assertEqual(len(self.r), 4)
    def test_iter_(self):
        i = iter(self.r)
        self.assertIsInstance(i, type(iter({})))
        c = {}
        for item in i:
            self.assertIn(item, self.r.map)
            c[item] = self.r.map[item]
        else:
            self.assertDictEqual(self.r.map, c)
    def test_get(self):
        self.assertDictEqual(self.r.get('A'), {'C': C, 'D': D})
        self.assertDictEqual(self.r.get('B'), {'D': D})
        self.assertDictEqual(self.r.get('C'), {})
        self.assertDictEqual(self.r.get('D'), {})

