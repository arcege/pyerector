#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

from .base import *

PyVersionCheck()

from pyerector.variables import Variable, VariableSet

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
        self.assertEqual(v.value, v.cache['property.A'])
        v = Variable('property.B')
        v.value = 'ni!'
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
    def test_transitive(self):
        v = Variable('transitive.A', 'spam')
        u = Variable('transitive.A')
        self.assertEqual(u.value, 'spam')

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

