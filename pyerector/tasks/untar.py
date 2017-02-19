#!/usr/bin/python
"""Tasks plugin for Untar."""

from ._base import Base
from ._container import Uncontainer

class Untar(Uncontainer, Base):
    """Extract a 'tar' archive file.
Untar(*files, name=<tarfilename>, root=None)"""
    def get_file(self, fname):
        """Open the container."""
        import tarfile
        return tarfile.open(str(self.join(fname)), 'r:gz')

    @staticmethod
    def retrieve_members(contfile, files):
        """Retrieve the members from the container."""
        import os
        fileset = []
        files = tuple(files)  # needed for contents test
        for member in contfile.getmembers():
            if (member.name.startswith(os.sep) or
                    member.name.startswith(os.pardir)):
                pass
            elif not files or member.name in files:
                fileset.append(member)
        return fileset

    def extract_members(self, contfile, fileset, root):
        """Extract members from the container."""
        for fileinfo in fileset:
            self.logger.debug('tar.extract(%s)', fileinfo.name)
            contfile.extract(fileinfo, path=(str(root) or ""))

Untar.register()
