#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

from .register import registry
from . import debug

# metaclass for instantiating Initer
class IniterMetaClass(type):
    def __init__(self, class_name, bases, namespace):
        type.__init__(self, class_name, bases, namespace)
        registry[class_name] = self
        debug('registering', self)

