#!/usr/bin/python
# Copyright @ 2012-2017 Michael P. Reilly. All rights reserved.

__all__ = [
    'Arguments',
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
    def items(self):
        return self.map.items()
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

class Arguments(object):
    """Gather a list of ArgumenType instances and process Python function
 arguments (*args, **kwargs) based on the what is passed to the class instance.
"""

    def __init__(self, *arglist):
        self.list = None
        self.map = {}
        for arg in arglist:
            if isinstance(arg, Arguments.List):
                if self.list is not None:
                    raise TypeError('Only one instance of Arguments.List allowed')
                elif arg.name in self.map:
                    raise TypeError('only one instance with the name %s allowed' % arg.name)
                self.list = arg
                self.map[arg.name] = arg
            elif isinstance(arg, Arguments.Keyword):
                if arg.name in self.map:
                    raise TypeError('only one instance with the name %s allowed' % arg.name)
                self.map[arg.name] = arg
            elif not isinstance(arg, Arguments.Type):
                raise TypeError('Must supply instance of Argument')

    def __add__(self, other):
        """Add two Arguments instances together, the left taking precedence;
the merge is performed based on the argument name."""
        # we take a copy of the other so self takes precedence
        map = other.map.copy()
        map.update(self.map)
        # handle corner case
        if self.list is not None and other.list is not None and \
           self.list != other.list:
            del map[other.list.name]
        return self.__class__(*map.values())

    def process(self, args, kwargs, existing=None):
        """Create a instance of ArgumentSet based on the values passed;
Exceptions raised on invalid data types or invalid keywords; defaults are
assigned as necessary."""
        assert isinstance(args, tuple)
        assert isinstance(kwargs, dict)
        if existing is not None:
            assert isinstance(existing, ArgumentSet)
            arglist = existing.list
            argmap = existing.map.copy()
        else:
            arglist = ()
            argmap = {}
        if self.list is not None:
            arglist = self.list.process(args)
            # we also add to the map:
            #List('name') === Keyword('name', type=tuple), with magic
            argmap[self.list.name] = arglist
        elif self.list is None and args:
            raise ValueError('not expecting positional arguments')
        # fill in the rest
        for name in self.map:
            if isinstance(self.map[name], Arguments.Keyword):
                argmap[name] = self.map[name].process(None)
        for name in kwargs:
            if name in self.map:
                argtype = self.map[name]
                argmap[name] = argtype.process(kwargs[name])
            else:
                raise ValueError('not a valid keyword: %s' % name)
        return ArgumentSet(arglist, argmap)

    class Type(object):
        """Allow processing of an argument with a given name and a defined type.
    Reject values that do not match the type or types."""
        def __init__(self, name, types=str, cast=None):
            self.name = name
            if isinstance(types, (list, tuple)):
                self.types = tuple(types)
                names = []
                for t in types:
                    if not isinstance(t, type):
                        raise TypeError('Must supply type for %s' % name)
                    names.append(t.__name__)
                self.typenames = ', '.join(names)
            elif not isinstance(types, type):
                raise TypeError('Must supply type for %s' % name)
            else:
                self.types = types
                self.typenames = types.__name__
            if cast is not None and not isinstance(cast, type):
                raise TypeError('Must supply cast type for %s' % name)
            elif cast is None:
                if isinstance(self.types, tuple):
                    cast = self.types[0]
                else:
                    cast = self.types
            elif (isinstance(self.types, tuple) and cast not in self.types) or \
                 (isinstance(self.types, type) and cast != self.types):
                raise ValueError('Cast must be one of types for %s' % name)
            self.cast = cast

        def process(self, value):
            """Validate the data type and process the value."""
            self.check_type(value)
            return self.process_value(value)

        def process_value(self, value):
            """Process the value, default is no change."""
            if self.cast is None:
                return value
            else:
                return self.cast(value)

        def check_type(self, value):
            """Raise an exception if the value is not one of the types given."""
            if not isinstance(value, self.types):
                raise TypeError('Value for %s requires %s' % (self.name, self.typenames))

    class List(Type):
        def check_type(self, value):
            """Raise an exception is one of the values in the list are not one
    of the types given."""
            assert isinstance(value, tuple)
            for v in value:
                super(Arguments.List, self).check_type(v)
        def process_value(self, value):
            results = []
            for v in value:
                results.append(super(Arguments.List, self).process_value(v))
            return tuple(results)

    class Keyword(Type):
        def __init__(self, name, types=str, default=None, noNone=False):
            super(Arguments.Keyword, self).__init__(name=name, types=types)
            if default is not None:
                super(Arguments.Keyword, self).check_type(default)
            self.default = default
            self.noNone = noNone

        def check_type(self, value):
            """If the value is None and noNone==True, then bypass the check
    If value is None and default is not None, then bypass the check."""
            if value is None and (not self.noNone or self.default is not None):
                return
            super(Arguments.Keyword, self).check_type(value)

        def process_value(self, value):
            """If the value is None and noNone==False, return default (which
    could be None).  If value is None and noNone==True, raise an exception.
    Otherwise return the value."""
            if value is None and not self.noNone:
                return self.default
            elif value is None and self.noNone:
                raise ValueError('None given for %s when noNone is expected' % self.name)
            else:
                return super(Arguments.Keyword, self).process_value(value)

