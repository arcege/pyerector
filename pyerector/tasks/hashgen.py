#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Tasks plugin for HashGen."""

from ..args import Arguments
from ._base import MapperTask
from ..iterators import FileIterator, FileMapper

def cast(value):
    """Cast appropriately: a sequence to a tuple, otherwise as a str."""
    if isinstance(value, (list, tuple, set)):
        return tuple(value)
    else:
        return (str(value),)

class HashGen(MapperTask):
    """Generate file(s) containing md5 or sha1 hash string.
For example, generates foobar.txt.md5 and foobar.txt.sha1 for the
contents of foobar.txt.  By default, generates for both md5 and sha1.
constructor arguments:
HashGen(*files, hashs=('md5', 'sha1'))"""
    arguments = Arguments(
        Arguments.Keyword('hashs', types=(tuple, str), default=('md5', 'sha1'),
                          cast=cast),
    ) + MapperTask.arguments

    def get_files(self, files=None, arg='files'):
        """Split the iterator into up to two mappers based on the hashs."""
        files = super(HashGen, self).get_files(files=files, arg=arg)
        fmap = FileIterator()
        # pylint: disable=no-member
        if 'md5' in self.args.hashs:
            fmap.append(FileMapper(files, mapper=lambda x: x.addext('.md5')))
        # pylint: disable=no-member
        if 'sha1' in self.args.hashs:
            fmap.append(FileMapper(files, mapper=lambda x: x.addext('.sha1')))
        return fmap

    def dojob(self, sname, dname, context):
        """Generate the appropriate hash file."""
        from hashlib import md5, sha1
        from ..helper import newer
        if dname.ext == '.md5':
            hashval = md5()
        elif dname.ext == '.sha1':
            # pylint: disable=redefined-variable-type
            hashval = sha1()
        else:
            self.logger.info('invalid extension on %s', dname)
            return
        if sname.isfile and newer(sname, dname):
            hashval.update(sname.open('rb').read())
            self.logger.debug('writing %s', dname)
            dname.open('wt').write(
                hashval.hexdigest() + '\n'
            )

HashGen.register()
