#!/usr/bin/python
"""Tasks plugin for HashGen."""

from ._base import Base
from ..args import Arguments
from ..base import Task
from ..iterators import FileMapper

class HashGen(Task, Base):
    """Generate file(s) containing md5 or sha1 hash string.
For example, generates foobar.txt.md5 and foobar.txt.sha1 for the
contents of foobar.txt.  By default, generates for both md5 and sha1.
constructor arguments:
HashGen(*files, hashs=('md5', 'sha1'))"""
    # pylint: disable=no-self-argument
    def cast(value):
        """Cast appropriately: a sequence to a tuple, otherwise as a str."""
        if isinstance(value, (list, tuple, set)):
            return tuple(value)
        else:
            return str(value)
    arguments = Arguments(
        Arguments.List('files'),
        Arguments.Keyword('hashs', types=(tuple, str), default=('md5', 'sha1'),
                          cast=cast),
    )

    def run(self):
        """Generate files with checksums inside."""
        from hashlib import md5, sha1
        files = self.get_files()
        # pylint: disable=no-member
        hashs = self.args.hashs
        self.logger.debug('files = %s; hashs = %s', files, hashs)
        fmaps = []
        if 'md5' in hashs:
            fmaps.append(
                (md5, FileMapper(files, mapper='%(name)s.md5'))
            )
        if 'sha1' in hashs:
            fmaps.append(
                (sha1, FileMapper(files, mapper='%(name)s.sha1'))
            )
        for hashfunc, fmap in fmaps:
            for sname, dname in fmap:
                hashval = hashfunc()
                sname = self.join(sname)
                dname = self.join(dname)
                self.logger.debug('HashGen.run: checkpair(%s, %s) = %s',
                                  sname, dname, fmap.checkpair(sname, dname))
                if sname.isfile and not fmap.checkpair(sname, dname):
                    hashval.update(sname.open('rb').read())
                    self.logger.debug('writing %s', dname)
                    dname.open('wt').write(
                        hashval.hexdigest() + '\n'
                    )

HashGen.register()
