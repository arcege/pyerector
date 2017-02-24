#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Tasks plugin for Zip."""

from zipfile import ZipFile

from ._container import Container

class Zip(Container):
    """Generate a 'zip' archive file.
Zip(*files, name=(containername), root=os.curdir, exclude=(defaults)."""
    def contain(self, name, root, toadd):
        """Add the files to the container."""
        try:
            self.logger.debug('Zip.contain(name=%s, root=%s, toadd=%s)',
                              repr(name), repr(root), repr(toadd))
            zfile = ZipFile(str(self.join(name)), 'w')
        except IOError:
            raise ValueError('no such file or directory: %s' % name)
        else:
            for fname in toadd:
                path = str(fname - root)
                self.logger.debug('zip.add(%s, %s)', fname, path)
                zfile.write(str(fname), path)
            zfile.close()

Zip.register()
