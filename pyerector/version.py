#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

from .variables import V


class VersionClass(object):
    def __init__(self):
        V['pyerector.vcs.version'] = '%hg.version%'
        V['pyerector.vcs.branch'] = '%hg.branch%'
        V['pyerector.vcs.tags'] = '%hg.tags%'
        V['pyerector.release.product'] = '%release.product%'
        V['pyerector.release.number'] = '%release.number%'

    @staticmethod
    def _validitem(item):
        return (
            item.startswith('pyerector.vcs.') or
            item.startswith('pyerector.release.')
        )

    def __getitem__(self, itemname):
        if self._validitem(itemname):
            return V[itemname]
        else:
            return KeyError(itemname)

    def __setitem__(self, itemname, value):
        if self._validitem(itemname):
            V[itemname] = value
        else:
            return KeyError(itemname)

    def __delitem__(self, itemname):
        raise NotImplementedError

    @property
    def version(self):
        v, b, t = (
            V('pyerector.vcs.version'),
            V('pyerector.vcs.branch'),
            V('pyerector.vcs.tags'),
        )
        version = v.value.replace('+', '')
        if b.value == 'default':
            branch = ''
        else:
            branch = ' (%s)' % b
        if t.value == 'tip':
            tags = ''
        else:
            tags = ' <%s>' % ','.join(t.value.split())
        return 'r%s%s%s' % (version, branch, tags)

    @property
    def release(self):
        return '%s %s' % (
            V('pyerector.release.product'),
            V('pyerector.release.number')
        )

HG_VERSION = '%hg.version%'
HG_BRANCH = '%hg.branch%'
HG_TAGS = '%hg.tags%'
RELEASE_PRODUCT = '%release.product%'
RELEASE_NUMBER = '%release.number%'

__all__ = [
    'Version',
]

Version = VersionClass()
