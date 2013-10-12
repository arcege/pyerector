#!/usr/bin/python

"""
Usage:
    Variable('name', 'value')
    Variable('name').value = 'value'
    print Variable('name')

    (Variable('name') == Variable('name'))
    (Variable('name1') < Variable('name2'))
    (hash(Variable('name')) == hash('name'))
    (Variable('name').name == 'name')
    (Variable('name').value == 'value)
    (Variable('name').toString() == Variable('name').name)
    (Variable('name').value is Variable('name').value)
    (Variable('name').value == str(Variable('name')))
    (V['name'] == Variable('name').value)
    (V('name') == Variable('name'))  # for backward compatibility

    # VariableSet is an augmented dictionary
    vs = VariableSet(
        Variable('name', 'michael'),
        Variable('number', '42'),
        Variable('address', '1313'),
        Variable('city', 'springfield')
    )
    (vs['name'] == Variable('name'))
    (vs['name'] == vs[Variable('name')])
    (vs == {Variable('name'): Variable('name'),
           Variable('number'): Variable('number'),
           Variable('address'): Variable('address'),
           Variable('city'): Variable('city')})
    (len(vs) == 4)
    (sorted(vs.keys()) == ['address', 'city', 'name', 'number']
    vs.add(Variable('zipcode', '00000'))
    vs.update(phone='888-555-1234')
    vs.update(('phone', '888-555-1234'))
    (vs['phone'] == 'phone')
    (vs['phone'].value == '888-555-1234')
    ('name' in vs == True)

"""

import logging
import threading

from .exception import Error

__all__ = [
    'V',
    'Variable',
    'VariableSet',
]

class VariableCache(object):
    """Mimic part of the functionality of a dictionary, but keep things
minimalistic.  And some functionality, like copy(), we don't want."""
    def __init__(self):
        self.cache = {}
        self.lock = threading.RLock()
    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.cache)
    def __len__(self):
        return len(self.cache)
    def __iter__(self):
        if hasattr(self.cache, 'iterkeys'):
            return self.cache.iterkeys()
        else:
            return iter(self.cache.keys())
    def __contains__(self, name):
        if not isinstance(name, Variable):
            name = Variable(name)
        with self.lock:
            return name in self.cache
    def __getitem__(self, name):
        if not isinstance(name, Variable):
            name = Variable(name)
        with self.lock:
            if name in self.cache:
                return self.cache[name]
            else:
                raise Error('no such variable: %s' % name.name)
    def __setitem__(self, name, value):
        if not isinstance(name, Variable):
            name = Variable(name)
        with self.lock:
            logger = logging.getLogger('pyerector.execute')
            try:
                logger.debug('name = %s; name.value = %s; value= %s', repr(name), repr(name.value), repr(value))
            except Error:
                logger.debug('name = %s; value = %s', repr(name), repr(value))
            self.cache[name] = value
    def __delitem__(self, name):
        if not isinstance(name, Variable):
            name = Variable(name)
        with self.lock:
            if name in self.cache:
                del self.cache[name]
            else:
                raise Error('no such variable: %s', name)
    def __call__(self, name, value=None):
        v = Variable(name)
        if value is not None:
            self[v] = value
        return v

V = VariableCache()

class Variable(str):
    cache = V
    def __new__(cls, name, value=None):
        return super(Variable, cls).__new__(cls, name)
    def __init__(self, name, value=None):
        if value is not None:
            self.cache[self] = value
    # this gets around the concatenating the name instead of the value
    def __add__(self, other):
        return self.value + other
    def __radd__(self, other):
        return other + self.value
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
        except Error:
            return ''
    @value.setter
    def value(self, value):
        self.cache[self] = value
    @value.deleter
    def value(self):
        del self.cache[self]
    @classmethod
    def list(cls):
        return tuple(cls.cache)

class VariableSet(dict):
    """A dictionary where all keys are variables and all values are the same
as the corresponding keys, i.e. {a: a, b: b, c: c, ...}"""
    def __new__(cls, *variables):
        # assign the variables in the initializer routine, not creater
        return super(VariableSet, cls).__new__(cls)
    def __init__(self, *variables):
        for var in variables:
            self.add(var)
    def add(self, var):
        if not isinstance(var, Variable):
            var = Variable(var)
        logging.debug('%s.add(%s)' % (self.__class__.__name__, repr(var)))
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
        logging.debug('setitem(%s, %s)' % (repr(item), repr(value)))
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

