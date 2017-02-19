#!/usr/bin/python
"""Tasks plugin for Unzip."""

from ._base import Base
from ._container import Uncontainer
from ..path import Path

class Unzip(Uncontainer, Base):
    """Extract a 'zip' archive file.
Unzip(*files, name=<tarfilename>, root=None)"""
    def get_file(self, fname):
        """Open the container."""
        from zipfile import ZipFile
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
