#!/usr/bin/python

"""
Usage:
    Variable('name', 'value')
    Variable('name').value = 'value'

    (Variable('name').value == Variable('name').value)
    (Variable('name').value == str(Variable('name')))
    print Variable('name')
"""

from . import debug
from .exception import Error

__all__ = [
    'Variable',
    'VariableSet',
]

class Variable(str):
    cache = {}  # a class variable
    def __new__(cls, name, value=None):
        return super(Variable, cls).__new__(cls, name)
    def __init__(self, name, value=None):
        if value is not None:
            self.cache[self] = value
    def __str__(self):
        return str(self.value)
    def __repr__(self):
        return 'Var(%s)' % super(Variable, self).__repr__()
    def toString(self):
        return super(Variable, self).__str__()
    @property
    def value(self):
        try:
            return self.cache[self]
        except KeyError:
            return ''
            #raise Error(self.toString())
    @value.setter
    def value(self, value):
        self.cache[self] = value
    @value.deleter
    def value(self):
        del self.cache[self]

class VariableSet(dict):
    def __new__(cls, *variables):
        # assign the variables in the initializer routine, not creater
        return super(VariableSet, cls).__new__(cls)
    def __init__(self, *variables):
        for var in variables:
            self.add(var)
    def add(self, var):
        if not isinstance(var, Variable):
            var = Variable(var)
        #print('%s.add(%s)' % (self.__class__.__name__, repr(var)))
        super(VariableSet, self).__setitem__(var, var)
    def __getitem__(self, item):
        if not isinstance(item, Variable):
            item = Variable(item)
        return super(VariableSet, self).__getitem__(item)
    def __setitem__(self, item, value):
        if not isinstance(item, Variable):
            item = Variable(item)
        if item not in self:
            self.add(item)
        #print('setitem(%s, %s)' % (repr(item), repr(value)))
        if item is not value: # didn't pass in the same object
            self[item].value = value
    def __delitem__(self, item):
        #del self[item].value  # also clear out the value?
        super(VariableSet, self).__delitem__(item)
    def update(self, *args, **kwargs):
        if hasattr(args, 'keys'):
            for k in args:
                self[k] = args[k]
        else:
            for (k, v) in args:
                self[k] = v
        for k in kwargs:
            self[k] = kwargs[k]

