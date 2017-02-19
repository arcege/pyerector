#!/usr/bin/python
"""Tasks plugin for Tar."""

from ._base import Base
from ._container import Container
from ..path import Path


class Tar(Container, Base):
    """Generate a 'tar' archive file.
Constructure arguments:
Tar(*files, name=None, root=os.curdir, exclude=(defaults)."""
    def contain(self, name, root, toadd):
        """Add a list of files to the container."""
        import tarfile
        try:
            tfile = tarfile.open(str(self.join(name)), 'w:gz')
        except IOError:
            raise ValueError('no such file or directory: %s' % name)
        else:
            for fname in toadd:
                if isinstance(fname, Path):
                    path = fname - root
                else:
                    path = Path(fname) - root
                self.logger.debug('tar.add(%s, %s)', fname, path)
                tfile.add(str(self.join(fname)), str(path))
            tfile.close()

Tar.register()
