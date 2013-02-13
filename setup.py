#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

from distutils.core import setup
import release

setup(
    name=release.product,
    version=release.number,
    description="Self-contained Python build library",
    long_description="Python module to create simplified build scripts",
    author="Michael P. Reilly",
    author_email="arcege@gmail.com",
    url="http://code.google.com/p/pyerector",
    packages=["pyerector", "pyerector/py2", "pyerector/py3"],
    download_url="http://code.google.com/p/pyerector/downloads/",
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
