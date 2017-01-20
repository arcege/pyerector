#!/usr/bin/python
# Copyright @ 2012-2017 Michael P. Reilly. All rights reserved.

__all__ = [
    'ArgumentSet',
    'ArgumentType',
    'ArgumentList',
    'ArgumentKeyword',
    'ArgumentHandler',
]

class ArgumentSet(object):
    """Access the arguments as either an iterable or an object (attributes)
or a dict."""
    def __init__(self, arglist, argmap):
        assert isinstance(arglist, tuple)
        assert isinstance(argmap, dict)
        self.list = arglist
        self.map = argmap

    def __getattr__(self, attr):
        if attr not in self.map:
            raise AttributeError(attr)
        return self.map[attr]
    def keys(self):
        return self.map.keys()
    def values(self):
        return self.map.values()

    def __iter__(self):
        return iter(self.list)
    def __len__(self):
        return len(self.list)
    def __getitem__(self, pos):
        if isinstance(pos, int):
            return self.list[pos]
        elif isinstance(pos, str):
            return self.map[pos]
        else:
            raise TypeError('expecting int or str')

    def combine(self, other, append=False):
        """Add the values from one ArgumentSet instance to this one.
If append==False, then replace the positional arguments, otherwise, append."""
        assert isinstance(other, ArgumentSet)
        if append:
            self.list += other.list
        else:
            self.list = other.list[:]
        self.map.update(other.map)

class ArgumentType(object):
    """Allow processing of an argument with a given name and a defined type.
Reject values that do not match the type or types."""
    def __init__(self, name, types=str):
        self.name = name
        self.types = types
        if isinstance(types, (list, tuple)):
            names = []
            for t in types:
                if not isinstance(t, type):
                    raise TypeError('Must supply type for %s' % name)
                names.append(t.__name__)
            self.typenames = ', '.join(names)
        else:
            if not isinstance(types, type):
                raise TypeError('Must supply type for %s' % name)
            self.typenames = types.__name__

    def process(self, value):
        """Validate the data type and process the value."""
        self.check_type(value)
        return self.process_value(value)

    def process_value(self, value):
        """Process the value, default is no change."""
        return value

    def check_type(self, value):
        """Raise an exception if the value is not one of the types given."""
        if not isinstance(value, self.types):
            raise TypeError('Value for %s requires %s' % (self.name, self.typenames))

class ArgumentList(ArgumentType):
    def check_type(self, value):
        """Raise an exception is one of the values in the list are not one
of the types given."""
        for v in value:
            super(ArgumentList, self).check_type(v)

class ArgumentKeyword(ArgumentType):
    def __init__(self, name, types=str, default=None, noNone=False):
        super(ArgumentKeyword, self).__init__(name=name, types=types)
        if default is not None:
            super(ArgumentKeyword, self).check_type(default)
        self.default = default
        self.noNone = noNone

    def check_type(self, value):
        """If the value is None and noNone==True, then bypass the check
If value is None and default is not None, then bypass the check."""
        if value is None and (not self.noNone or self.default is not None):
            return
        super(ArgumentKeyword, self).check_type(value)

    def process_value(self, value):
        """If the value is None and noNone==False, return default (which
could be None).  If value is None and noNone==True, raise an exception.
Otherwise return the value."""
        if value is None and not self.noNone:
            return self.default
        elif value is None and self.noNone:
            raise ValueError('None given for %s when noNone is expected' % self.name)
        else:
            return value

class ArgumentHandler(object):
    """Gather a list of ArgumenType instances and process Python function
 arguments (*args, **kwargs) based on the what is passed to the class instance.
"""
    def __init__(self, *arglist):
        self.typelist = None
        self.typemap = {}
        self.arglist = None
        self.argmap = {}
        for arg in arglist:
            if isinstance(arg, ArgumentList):
                if self.typelist is not None:
                    raise TypeError('Only one instance of ArgumentList allowed')
                self.typelist = arg
            elif isinstance(arg, ArgumentKeyword):
                if arg.name in self.typemap:
                    raise TypeError('only one instance of ArgumentKeyword with %s allowed' % arg.name)
                self.typemap[arg.name] = arg
            elif not isinstanace(arg, ArgumentType):
                raise TypeError('Must supply instance of Argument')

    def process(self, args, kwargs):
        """Create a instance of ArgumentSet based on the values passed;
Exceptions raised on invalid data types or invalid keywords; defaults are
assigned as necessary."""
        assert isinstance(args, tuple)
        assert isinstance(kwargs, dict)
        arglist = None
        argmap = {}
        if self.typelist is not None and args:
            arglist = self.typelist.process(args)
        elif self.typelist is None and args:
            raise ValueError('not expecting positional arguments')
        for name in kwargs:
            if name in self.typemap:
                argtype = self.typemap[name]
                argmap[name] = argtype.process(kwargs[name])
            else:
                raise ValueError('not a valid keyword: %s' % name)
        # fill in the rest
        for name in self.typemap:
            argmap[name] = self.typemap[name].process(None)
        return ArgumentSet(arglist, argmap)

