#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Tasks plugin for Download."""

from ..args import Arguments
from ..path import Path
from ._base import Task

class Download(Task):
    """Retrieve contents of URLs.
constructor arguments:
Download(*urls, destdir=DIR)"""
    dest = None
    urls = ()
    def run(self):
        # this is unfinished, it requires a more generic Mapper class
        # than one is available now
        """
        import urllib
        from posixpath import basename
        from .iterators import BaseIterator
        urls = self.get_files(self.get_args('urls'))
        urls = BaseIterators(self.get_args('urls'), noglob=True, fileonly=False)

        dest = self.get_kwarg('dest', str)
        if isinstance(urls, str):
            urls = (urls,)
        if isinstance(urls, FileMapper):
            urls = urls
        elif isinstance(dest, str) and os.path.isdir(dest):
            urls = BasenameMapper(urls, destdir=dest,
                                  mapper=lambda x: x or 'index.html')
        elif isinstance(dest, str):
            urls = IdentityMapper(urls, destdir=dest)
        else:
            urls = FileMapper(urls, destdir=dest)
        for url, fname in urls:
            path = urllib.splithost(urllib.splittype(url)[1])[1]
            self.logger.debug('Download.path=%s; Download.fname=%s',
                              path, fname)
            try:
                urllib.urlretrieve(url, filename=fname)
            except Exception, e:
                raise Error(str(self), '%s: unable to retrieve %s' % (e, url))
        """
        raise NotImplementedError

Download.register()
