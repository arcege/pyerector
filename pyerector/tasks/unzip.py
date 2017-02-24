#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Tasks plugin for Unzip."""

from zipfile import ZipFile

from ._container import Uncontainer

class Unzip(Uncontainer):
    """Extract a 'zip' archive file.
Unzip(*files, name=<tarfilename>, root=None)"""
    def get_file(self, fname):
        """Open the container."""
        return ZipFile(str(self.join(fname)), 'r')

    @staticmethod
    def retrieve_members(contfile, files):
        """Retrieve the members from the container."""
        import os
        fileset = []
        files = tuple(files)  # needed for contents test
        for member in contfile.namelist():
            if member.startswith(os.sep) or member.startswith(os.pardir):
                pass
            elif not files or member in files:
                fileset.append(member)
        return fileset

    def extract_members(self, contfile, fileset, root):
        """Extract members from the container."""
        for member in fileset:
            dname = root + member
            if not dname.dirname.isdir:
                dname.dirname.mkdir()
            self.logger.debug('zip.extract(%s)', member)
            dfile = dname.open('wb')
            dfile.write(contfile.read(member))

Unzip.register()
