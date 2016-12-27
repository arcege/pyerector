=========
PyErector
=========
An Erector set for building systems
-----------------------------------

PyErector is more clear and Pythonic than using Distutils, but not as deep.

The idea is to organize the work to be done in tasks (work units) and targets
(organizational units).  Targets can specify tasks to work on, or override the
default operation (does nothing) and specify dependencies.  Tasks can specify
files or data to perform specialized operations on (Copy, Tar, etc.).
Objects are classes and can be subclassed to create new work flows.

Installation
============

Using pip
---------
Run ``pip pyerector`` to install inthe Python's distribution from pypi.

Using file copy
---------------
Copy the ``pyerector`` structure into the project directory, then create a
``pyerect`` script using the structure as a library.

Using distutils
---------------
Run the ``./setup.py install`` to install into Python's distribution.

Starting out
============
PyErector is a library used by any program to create tasks and targets for
performing build management steps.  Traditionally, the main program is called
``pyerect``, but it can be any executable Python script.

Start by importing from ``pyerector``::

  #!/usr/bin/python
  from pyerector import *

Next modify attributes of standard targets::

  Compile.tasks = (
      PyCompile(FileIterator('src', pattern='*.py')),
  )

Lastly, call the main routine::

  PyErector()

This small program would generate pyc files for each of the Python source
files found under the ``src`` directory.

Documentation
=============
Please visit the `project site <https://bitbucket.org/Arcege/pyerector/wiki/>`_
for documentation.

----
Copyright (C) 2010-2016 Michael P. Reilly.  All rights reserved.
