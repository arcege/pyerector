#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.
"""Need an easy way to map a class name (string) to the class.  The
metaclass here will use a global registry for the mapping.
"""

import logging
from .register import registry

# metaclass for instantiating Initer


class IniterMetaClass(type):
    """Meta class to register the class for easy retrieval later."""
    def __init__(cls, class_name, bases, namespace):
        type.__init__(cls, class_name, bases, namespace)
        registry[class_name] = cls
        logging.debug('registering %s', cls)

