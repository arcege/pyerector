#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Tasks plugin for Egg."""

import os

from ..path import Path
from ..exception import Error
from .zip import Zip

class Egg(Zip):
    """Generate an egg file for Python deployments.
Egg(*files, name=<eggfilename>, root=os.curdir, exclude=(defaults))"""
    def manifest(self, name, root, toadd):
        """Generate a manifest structure."""
        fname = Path(name).basename
        fname.delext()
        pos = str(fname).find('-')
        if pos != -1:
            fname = Path(str(fname)[:pos])
        eggdir = root + 'EGG-INFO'
        try:
            eggdir.mkdir()
        except OSError:
            pass
        self.do_file_pkginfo(eggdir, toadd, root)
        self.do_file_dummy(eggdir, toadd, 'dependency_links.txt')
        self.do_file_dummy(eggdir, toadd, 'zip-safe')
        self.do_file_top_level(eggdir, toadd, fname)
        self.do_file_sources(eggdir, toadd, root)

    @staticmethod
    def add_path(seq, path):
        """Add a path if not in the sequence."""
        if path not in seq:
            seq.append(path)

    def do_file_dummy(self, rootdir, toadd, fname):
        """Create an empty file."""
        fname = rootdir + fname
        fname.open('wt').write(os.linesep)
        self.add_path(toadd, fname)
    def do_file_top_level(self, rootdir, toadd, name):
        """Generate top_level.txt file."""
        fname = rootdir + 'top_level.txt'
        fname.open('wt').write(str(name) + os.linesep)
        self.add_path(toadd, fname)
    def do_file_sources(self, rootdir, toadd, root):
        """Generate SOURCES.txt files."""
        fname = rootdir + 'SOURCES.txt'
        with fname.open('wt') as fobj:
            for sfname in sorted([s - root for s in toadd]):
                if sfname.basename != 'EGG-INFO':
                    fobj.write(str(sfname) + os.linesep)
        self.add_path(toadd, fname)
    # pylint: disable=unused-argument
    def do_file_pkginfo(self, rootdir, toadd, root):
        """Generate the PKG-INFO file."""
        fname = root + 'setup.py'
        if fname.exists:
            setupvalue = self.get_setup_py(fname)
        else:
            raise Error('Egg', 'unable to find a setup.py file')
        pkg_data = {
            'classifiers': '',
        }
        for key in sorted(setupvalue):
            if key == 'classifiers':
                pkg_data[key] = '\n'.join(
                    ['Classifier: %s' % c for c in setupvalue[key]]
                )
            else:
                pkg_data[key] = setupvalue[key]
        pkg_info = '''\
Metadata-Version: 1.1
Name: %(name)s
Version: %(version)s
Summary: %(description)s
Home-page: %(url)s
Author: %(author)s
Author-email: %(author_email)s
License: %(license)s
Download-URL: %(download_url)s
Description: %(long_description)s
Platform: UNKNOWN
%(classifiers)s
''' % pkg_data
        eggdir = root + 'EGG-INFO'
        try:
            eggdir.mkdir()
        except OSError:
            pass
        fname = eggdir + 'PKG-INFO'
        fname.open('wt').write(pkg_info)
        if fname not in toadd:
            toadd.append(fname)
        for fname in ('depenency_links.txt', 'zip-safe'):
            fname = eggdir + fname
            fname.open('wt').write(os.linesep)
            if fname not in toadd:
                toadd.append(fname)
        fname = eggdir + 'top_level.txt'
        fname.open('wt').write('pyerector' + os.linesep)
        if fname not in toadd:
            toadd.append(fname)
        fname = eggdir + 'SOURCES.txt'
        fname.open('wt').write(
            os.linesep.join(sorted(
                [str(s - root) for s in toadd
                 if s.basename != 'EGG-INFO']
            )) + os.linesep
        )
        if fname not in toadd:
            toadd.append(fname)
        # convert Path instances to a str
        toadd[:] = [str(f) for f in toadd]

    @staticmethod
    def get_setup_py(filename):
        """Simulate setup() in a fake distutils and setuptools."""
        import imp
        import sys
        backups = {}
        script = '''
def setup(**kwargs):
    global myvalue
    myvalue = dict(kwargs)
'''
        code = compile(script, 'setuptools.py', 'exec')
        try:
            for modname in ('setuptools', 'distutils'):
                if modname in sys.modules:
                    backups[modname] = sys.modules[modname]
                else:
                    backups[modname] = None
                mod = sys.modules[modname] = imp.new_module(modname)
                # pylint: disable=exec-used
                exec(code, mod.__dict__, mod.__dict__)
            mod = {'__builtins__': __builtins__, 'myvalue': None}
            execfile(str(filename), mod, mod)
            for modname in ('setuptools', 'distutils'):
                if sys.modules[modname].myvalue is not None:
                    return sys.modules[modname].myvalue
            return None
        finally:
            for modname in backups:
                if backups[modname] is None:
                    del sys.modules[modname]
                else:
                    sys.modules[modname] = backups[modname]

Egg.register()
