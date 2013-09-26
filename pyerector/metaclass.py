#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import logging
from .register import registry

# metaclass for instantiating Initer
class IniterMetaClass(type):
    def __init__(self, class_name, bases, namespace):
        type.__init__(self, class_name, bases, namespace)
        registry[class_name] = self
        logging.debug('registering %s', self)

