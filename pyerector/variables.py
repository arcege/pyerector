#!/usr/bin/python

"""
Usage:
    Variable('name', 'value')
    Variable('name').value = 'value'

    (Variable('name').value == Variable('name').value)
    (Variable('name').value == str(Variable('name')))
    print Variable('name')
"""

from . import display, debug
from .exception import Error
from . import version

__all__ = [
    'Variable',
    'VariableSet',
]

class Variable(str):
    """A global variable.
Usage:
    Variable('name', 'value')
    Variable('name').value = 'value'
    (Variable('name').value is Variable('name').value)
    (Variable('name').value == str(Variable('name'))
    print Variable('name')
"""
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
        return self.name  # use the 'name' property
    @property
    def name(self):
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
    @classmethod
    def list(cls):
        return tuple(cls.cache)

# initialize some variables
Variable('pyerector.release.product', version.RELEASE_PRODUCT)
Variable('pyerector.release.number', version.RELEASE_NUMBER)
Variable('pyerector.vcs.version', version.HG_VERSION)
Variable('pyerector.vcs.branch', version.HG_BRANCH)
Variable('pyerector.vcs.tags', version.HG_TAGS)

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
        #display('%s.add(%s)' % (self.__class__.__name__, repr(var)))
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
        #display('setitem(%s, %s)' % (repr(item), repr(value)))
        if item is not value: # didn't pass in the same object
            self[item].value = value
    def __delitem__(self, item):
        #del self[item].value  # also clear out the value?
        super(VariableSet, self).__delitem__(item)
    def update(self, *args, **kwargs):
        # how would args have 'keys' when it is a tuple?
        if hasattr(args, 'keys'):
            for k in args:
                self[k] = args[k]
        else:
            for (k, v) in args:
                self[k] = v
        for k in kwargs:
            self[k] = kwargs[k]

