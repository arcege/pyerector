#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.

from setuptools import setup
import os
import release
import sys

program = sys.argv[0]
progdir = os.path.dirname(program)
# do not run if from the source directory
if __name__ == '__main__' and os.path.exists(os.path.join(progdir, 'pyerect')):
    raise SystemExit('please run "pyerect" instead of %s.' % sys.argv[0])

setup(
    name=release.product,
    version=release.number,
    description="Self-contained Python build library",
    long_description="Python module to create simplified build scripts",
    author="Michael P. Reilly",
    author_email="arcege@gmail.com",
    url="http://bitbucket.org/Arcege/pyerector",
    packages=[
        "pyerector", "pyerector.py2", "pyerector.py3", "pyerector.vcs",
    ],
    download_url="http://pypi.python.org/pypi/pyerector",
    license=
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Build Tools",
    ],
)
