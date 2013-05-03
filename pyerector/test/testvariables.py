#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

from .base import PyVersionCheck, TestCase

PyVersionCheck()

from pyerector.variables import V, VariableCache, Variable, VariableSet

class TestVariableCache(TestCase):
    def setUp(self):
        self.oldvc = Variable.cache
        self.vc = VariableCache()
        Variable.cache = self.vc
    def tearDown(self):
        Variable.cache = self.oldvc
    def test_init_(self):
        self.assertEqual(self.vc.cache, {})
    def test_cache(self):
        class A:
            pass
        self.vc.cache[Variable('a')] = A # for uniqueness
        self.assertIs(self.vc.cache['a'], A)  # access by string
        self.assertIs(self.vc.cache[Variable('a')], A)
    def test_len_(self):
        self.assertEqual(len(self.vc), 0)
        self.vc['a'] = 512
        self.assertEqual(len(self.vc), 1)
        self.vc['b'] = 'bye'
        self.vc['c'] = 'hi'
        self.vc['xyzzy'] = 'what?'
        self.assertEqual(len(self.vc), 4)
    def test_iter_(self):
        # type(iter({})) is not type(iter(''))
        if hasattr({}, 'iterkeys'): # python2
            self.assertIsInstance(iter(self.vc), type({}.iterkeys()))
        else:
            self.assertIsInstance(iter(self.vc), type(iter({}.keys())))
        self.assertEqual(list(self.vc), [])
        self.vc['a'] = 512
        self.assertEqual(list(self.vc), [Variable('a')])
    def test_contains_string(self):
        self.vc.cache[Variable('a')] = 'bye'
        self.assertIn('a', self.vc)
    def test_contains_string_not(self):
        self.vc.cache[Variable('a')] = 'bye'
        self.assertNotIn('b', self.vc)
    def test_contains_variable(self):
        self.vc.cache[Variable('a')] = 'bye'
        self.assertIn(Variable('a'), self.vc)
    def test_contains_variable_not(self):
        self.vc.cache[Variable('a')] = 'bye'
        self.assertNotIn(Variable('b'), self.vc)
    def test_getitem_empty(self):
        with self.assertRaises(KeyError):
            self.vc['notpresent']
            self.vc[Variable('nosuchvariable')]
    def test_getitem_wrong_string(self):
        self.vc.cache[Variable('a')] = 'hi'
        with self.assertRaises(KeyError):
            self.vc['c']
    def test_getitem_wrong_variable(self):
        self.vc.cache[Variable('a')] = 'hi'
        with self.assertRaises(KeyError):
            self.vc[Variable('c')]
    def test_getitem_string(self):
        self.vc.cache[Variable('a')] = 'hi'
        self.assertEqual(self.vc['a'], 'hi')
    def test_getitem_variable(self):
        self.vc.cache[Variable('a')] = 'hi'
        self.assertEqual(self.vc[Variable('a')], 'hi')
    def test_setitem_string_string(self):
        self.vc['a'] = 'abcde'
        self.assertEqual(self.vc.cache['a'], 'abcde')
    def test_setitem_string_int(self):
        self.vc['a'] = 612
        self.assertEqual(self.vc.cache['a'], 612)
    def test_setitem_variable_string(self):
        self.vc[Variable('a')] = 'abcde'
        self.assertEqual(self.vc.cache['a'], 'abcde')
    def test_setitem_variable_int(self):
        self.vc[Variable('a')] = 521
        self.assertEqual(self.vc.cache['a'], 521)
    def test_setitem_string_variable(self):
        v = Variable('abcde')
        self.vc['a'] = v
        self.assertIs(self.vc.cache['a'], v)
    def test_setitem_variable_variable(self):
        v = Variable('abcde')
        self.vc[Variable('a')] = v
        self.assertIs(self.vc.cache['a'], v)
    def test_setitem_samevalues(self):
        v = Variable('xyzzy')
        self.vc[v] = v
        self.assertIs(self.vc.cache[v], v)
    def test_setitem_overstrike(self):
        v = Variable('xyzzy')
        self.vc[v] = 'a'
        self.assertEqual(self.vc.cache['xyzzy'], 'a')
        self.vc[v] = 'b'
        self.assertEqual(self.vc.cache['xyzzy'], 'b')
    def test_delitem_string(self):
        self.vc.cache[Variable('a')] = 'abcde'
        self.assertIn('a', self.vc.cache)
        del self.vc['a']
        self.assertNotIn('a', self.vc.cache)
    def test_delitem_variable(self):
        self.vc.cache[Variable('a')] = 'abcde'
        self.assertIn('a', self.vc.cache)
        del self.vc[Variable('a')]
        self.assertNotIn('a', self.vc.cache)
    def test_call_(self):
        self.assertIsInstance(self.vc('a'), Variable)

class TestV(TestCase):
    def test_V(self):
        self.assertIsInstance(V, VariableCache)
        #self.assertEqual(V.cache, {})

class TestVariable(TestCase):
    def test_new_(self):
        v = Variable('new.A')
        self.assertIs(v.cache, Variable.cache)
        self.assertNotIn('new.A', v.cache)
        v = Variable('new.B', 'spam')
        self.assertIn('new.B', v.cache)
        self.assertEqual(v.cache['new.B'], 'spam')
    def test_property(self):
        v = Variable('property.A', 'spam')
        self.assertEqual(v.name, 'property.A')
        self.assertEqual(v.value, v.cache['property.A'])
        v = Variable('property.B')
        v.value = 'ni!'
        self.assertEqual(v.name, 'property.B')
        self.assertEqual(v.value, v.cache['property.B'])
        self.assertEqual(v.value, 'ni!')
        v = Variable('property.C', 'ippy ippy thuang zooop!')
        self.assertEqual(v.cache['property.C'], 'ippy ippy thuang zooop!')
        del v.value
        self.assertNotIn('property.C', v.cache)
        self.assertEqual(v.value, '')
    def test_strrepr(self):
        v = Variable('strrepr.A', 'spam')
        self.assertEqual(str(v), 'spam')
        self.assertEqual(repr(v), "Var('strrepr.A')")
        self.assertEqual(v.toString(), 'strrepr.A')
    def test_reflexive(self):
        v = Variable('transitive.A', 'spam')
        u = Variable('transitive.A')
        self.assertEqual(u.value, 'spam')
    def test_transitive(self):
        v = Variable('transitive.A', 'spam')
        w = Variable('transitive.B', v)
        self.assertEqual(w.value, v)
        self.assertEqual(str(w), 'spam')

class TestVariableSet(TestCase):
    def test_new_(self):
        # empty
        vs = VariableSet()
        self.assertDictEqual(vs, {})
        # populate with Variable instances
        vs = VariableSet(
                Variable('new_.A'), Variable('new_.B', 'spam'),
                Variable('new_.C', 'ni!'), Variable('new_.D')
        )
        self.assertDictEqual(vs,
            { Variable('new_.A'): Variable('new_.A'),
              Variable('new_.B'): Variable('new_.B'),
              Variable('new_.C'): Variable('new_.C'),
              Variable('new_.D'): Variable('new_.D'),
            }
        )
        # populate with strings, not Variable instances
        vs = VariableSet('new_.A', 'new_.B', 'new_.C', 'new_.D')
        self.assertDictEqual(vs,
            { Variable('new_.A'): Variable('new_.A'),
              Variable('new_.B'): Variable('new_.B'),
              Variable('new_.C'): Variable('new_.C'),
              Variable('new_.D'): Variable('new_.D'),
            }
        )
    def test_add(self):
        vs = VariableSet()
        # add a variable
        vs.add(Variable('add.A'))
        self.assertDictEqual(vs, {Variable('add.A'): Variable('add.A')})
        # variable with value, doesn't change things
        vs.add(Variable('add.B', 'spam'))
        self.assertDictEqual(vs,
                { Variable('add.A'): Variable('add.A'),
                  Variable('add.B'): Variable('add.B'),
                }
        )
        # string instead of Variable
        vs.add('add.C')
        self.assertDictEqual(vs,
                { Variable('add.A'): Variable('add.A'),
                  Variable('add.B'): Variable('add.B'),
                  Variable('add.C'): Variable('add.C'),
                }
        )
    def test_getitem_(self):
        vs = VariableSet(
                Variable('getitem_.A'),
                Variable('getitem_.B', 'spam'),
                Variable('getitem_.C', 'ni!'),
        )
        # retrieve by difference instance with same 'string'
        self.assertEqual(vs[Variable('getitem_.A')], Variable('getitem_.A'))
        # string instead of variable
        self.assertEqual(vs['getitem_.C'], Variable('getitem_.C'))
    def test_setitem_(self):
        vs = VariableSet(Variable('setitem_.C', 'ni!'))
        # set value on new Variable to set
        vs[Variable('setitem_.A')] = 'spam'
        self.assertIn('setitem_.A', vs)
        self.assertEqual(Variable('setitem_.A').value, 'spam')
        # set value using string instead of variable
        vs['setitem_.B'] = 'ni!'
        self.assertIn(Variable('setitem_.B'), vs)
        self.assertEqual(Variable('setitem_.B').value, 'ni!')
        # already existing variable
        vs['setitem_.C'] = 'ippy ippy thuang zooop!'
        self.assertIn(Variable('setitem_.C'), vs)
        self.assertEqual(Variable('setitem_.C').value,
                         'ippy ippy thuang zooop!')
    def test_delitem_(self):
        vs = VariableSet(
                Variable('delitem_.A'),
                Variable('delitem_.B', 'spam'),
                Variable('delitem_.C', 'ni!'),
        )
        del vs[Variable('delitem_.A')]
        self.assertNotIn(Variable('delitem_.A'), vs)
        del vs['delitem_.B']
        self.assertNotIn(Variable('delitem_.B'), vs)
        self.assertDictEqual(vs,
                {Variable('delitem_.C'): Variable('delitem_.C')}
        )
    def _test_update(self):
        pass

