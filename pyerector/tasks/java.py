#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Tasks plugin for Java."""

import os

from ..path import Path
from ..exception import Error
from ..helper import Subcommand
from ._base import Task

class Java(Task):
    """Call a Java routine.
constructor arguments:
Java(jar=<JAR>, java_home=<$JAVA_HOME>, classpath=(), properties=[])"""
    from os import environ
    try:
        java_home = environ['JAVA_HOME']
    except KeyError:
        java_home = None
    classpath = ()
    properties = []
    del environ
    jar = None

    def __init__(self, *args, **kwargs):
        super(Java, self).__init__(*args, **kwargs)
        if self.java_home and os.path.exists(str(self.java_home)):
            self.java_prog = os.path.join(str(self.java_home), 'bin', 'java')
        elif os.path.exists(os.path.expanduser(os.path.join('~', 'java'))):
            self.java_prog = os.path.expanduser(
                os.path.join('~', 'java', 'bin', 'java')
            )
        else:
            raise Error("no java program to execute")
        if not os.access(str(self.java_prog), os.X_OK):
            raise Error("no java program to execute")

    def addprop(self, var, val):
        """Add a Java system property to the list."""
        self.properties.append((var, val))

    def run(self):
        """Call java."""
        from os import environ
        from os.path import pathsep
        jar = self.get_kwarg('jar', (Path, str), noNone=True)
        if self.properties:
            sysprop = ['-D%s=%s' % x for x in self.properties]
        else:
            sysprop = ()
        cmd = (self.java_prog,) + tuple(sysprop) + \
            ('-jar', str(jar),) + \
            tuple([str(s) for s in self.args])
        env = environ.copy()
        if self.classpath:
            env['CLASSPATH'] = pathsep.join(self.classpath)
        proc = Subcommand(cmd)
        if proc.returncode:
            raise Error(self, '%s failed with returncode %d' %
                        (self.__class__.__name__.lower(), proc.returncode)
                       )

Java.register()
