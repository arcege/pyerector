#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Tasks plugin for Untar."""

import tarfile

from ._container import Uncontainer

class Untar(Uncontainer):
    """Extract a 'tar' archive file.
Untar(*files, name=<tarfilename>, root=None)"""
    def get_file(self, fname):
        """Open the container."""
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
