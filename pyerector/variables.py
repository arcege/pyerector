#!/usr/bin/python
# Copyright @ 2013-2017 Michael P. Reilly. All rights reserved.
"""
Usage:
    Variable('name', 'value')
    Variable('name').value = 'value'
    print Variable('name')

    (Variable('name') == Variable('name'))
    (Variable('name1') < Variable('name2'))
    (hash(Variable('name')) == hash('name'))
    (Variable('name').name == 'name')
    (Variable('name').value == 'value')
    (Variable('name').toString() == Variable('name').name)  # deprecated
    (Variable('name').value is Variable('name').value)
    (Variable('name').value == str(Variable('name')))
    (V['name'] == Variable('name').value)
    (V('name') == Variable('name'))  # for backward compatibility

    fv = FileVariable('file', 'test.txt')
    (Variable('file').value == 'test.txt')
    fv.value == open('test.txt', 'rt').read().decode('UTF-8')
    fv.value = 'test2.txt'
    (Variable('file').value == 'test2.txt')
    fv.value != open('test.txt', 'rt').read().decode('UTF-8')

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
    vs1 = VariableSet(
        Variable('email': 'michael@springfield.us')
    )
    vs1.update(vs)
    (vs1['name'] == Variable('name'))
    ('email' not in vs and 'email' in vs1)

"""

import logging
import threading

from .exception import Error

__all__ = [
    'FileVariable',
    'V',
    'Variable',
    'VariableSet',
]


# pylint: disable=too-few-public-methods
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
            #logger = logging.getLogger('pyerector.execute')
            # to prevent a really long string, just the first 25 characters
            #s = repr(value)
            #if len(s) > 25:
            #    logger.debug('name = %s; value = %s', repr(name),
            #        s[:25] + '...' + s[-1:])
            #else:
            #    logger.debug('name = %s; value= %s', repr(name), s)
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
        var = Variable(name)
        if value is not None:
            self[var] = value
        return var

V = VariableCache()


class Variable(str):
    """Create a persistent string with a mutable value."""
    cache = V

    # pylint: disable=unused-argument
    def __new__(cls, name, value=None):
        return super(Variable, cls).__new__(cls, name)

    # pylint: disable=unused-argument
    def __init__(self, name, value=None):
        super(Variable, self).__init__()
        if value is not None:
            self.cache[self] = value

    # this gets around the concatenating the name instead of the value
    def __add__(self, other):
        return self.value + other

    def __radd__(self, other):
        return other + self.value

    def __str__(self):
        """Return the value instead of the name."""
        return str(self.value)

    def __repr__(self):
        return 'Var(%s)' % super(Variable, self).__repr__()

    def toString(self):
        """Deprecated."""
        return self.name  # use the 'name' property

    @property
    def name(self):
        """Return the string (name)."""
        return super(Variable, self).__str__()

    def retrieve_value(self):
        """Return the cache value or an empty string."""
        try:
            return self.cache[self]
        except Error:
            return ''

    @property
    def value(self):
        """Retrieve the value from the cache."""
        return self.retrieve_value()

    @value.setter
    def value(self, value):
        """Change the value in the cache."""
        self.cache[self] = value

    @value.deleter
    def value(self):
        """Delete the variable from the cache."""
        del self.cache[self]

    @classmethod
    def list(cls):
        """Return the cache as a tuple (not a list)."""
        return tuple(cls.cache)


class FileVariable(Variable):
    """Load a variables value from a file, but only when we need it.
Setting to the value changes the filename, getting the value reads the file.
File contents are decoded by default as UTF-8."""
    encoding = 'UTF-8'

    # pylint: disable=arguments-differ
    @classmethod
    def encode(cls, data):
        return data.encode(cls.encoding)

    # pylint: disable=arguments-differ
    @classmethod
    def decode(cls, data):
        return data.decode(cls.encoding)

    @staticmethod
    def read(fileobj):
        """Read data from the file object."""
        return fileobj.read()

    @staticmethod
    def write(fileobj, data):
        """Write data to the file object."""
        fileobj.write(data)

    @property
    def filename(self):
        """The file that the variable represents."""
        try:
            return self.cache[self]
        except Error:
            return ''

    @filename.setter
    def filename(self, value):
        self.cache[self] = value

    @filename.deleter
    def filename(self):
        del self.cache[self]

    @property
    def value(self):
        import sys
        try:
            with open(str(self.filename), 'rt') as infile:
                contents = self.decode(self.read(infile))
        except IOError:
            raise ValueError('%s: %s' % (self.filename, sys.exc_info()[1]))
        return contents

    @value.setter
    def value(self, value):
        import sys
        try:
            with open(str(self.filename), 'wt') as outfile:
                self.write(outfile, self.encode(value))
        except IOError:
            raise ValueError('%s: %s' % (self.filename, sys.exc_info()[1]))

    @value.deleter
    def value(self):
        import os
        try:
            os.remove(str(self.filename))
        except OSError:
            raise ValueError('cannot delete')


class VariableSet(dict):
    """A dictionary where all keys are variables and all values are the same
as the corresponding keys, i.e. {a: a, b: b, c: c, ...}"""
    # pylint: disable=unused-argument
    def __new__(cls, *variables, **kwargs):
        # assign the variables in the initializer routine, not creater
        return super(VariableSet, cls).__new__(cls)

    def __init__(self, *variables, **kwargs):
        super(VariableSet, self).__init__()
        for var in variables:
            self.add(var)
        for kword in kwargs:
            self.add(kwargs[kword])

    def add(self, var):
        """Add a new variable to the set."""
        if not isinstance(var, Variable):
            var = Variable(var)
        logging.debug('%s.add(%s)', self.__class__.__name__, repr(var))
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
        logging.debug('setitem(%s, %s)', repr(item), repr(value))
        if item is not value:  # didn't pass in the same object
            self[item].value = value

    def __delitem__(self, item):
        #del self[item].value  # also clear out the value?
        super(VariableSet, self).__delitem__(item)

    def update(self, *args, **kwargs):
        """Augment the set with additional values."""
        for datum in args:
            if hasattr(datum, 'keys'):
                for name in datum:
                    self[name] = datum[name]
            else:
                for (name, value) in datum:
                    self[name] = value
        for name in kwargs:
            self[name] = kwargs[name]

