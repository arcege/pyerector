#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.
"""Hold the version control information about the product.
The build replaces the %..% tokens with proper values.
The constants (HG_* and RELEASE_*) at the end are for backward compatibility.
"""

from .variables import V


class VersionClass(object):
    """Define variables with version/release information and
retrieve using this interface."""
    def __init__(self):
        V['pyerector.release.version'] = '%hg.version%'
        V['pyerector.release.branch'] = '%hg.branch%'
        V['pyerector.release.tags'] = '%hg.tags%'
        V['pyerector.release.product'] = '%release.product%'
        V['pyerector.release.number'] = '%release.number%'

    @staticmethod
    def _validitem(item):
        """Ensure that the variable name is valid."""
        return (
            item.startswith('pyerector.vcs.') or
            item.startswith('pyerector.release.')
        )

    def __len__(self):
        return 5

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
        """Retrieve the version control information."""
        vstr, bstr, tstr = (
            V('pyerector.release.version'),
            V('pyerector.release.branch'),
            V('pyerector.release.tags'),
        )
        version = vstr.value.replace('+', '')
        if bstr.value == 'default':
            branch = ''
        else:
            branch = ' (%s)' % bstr
        if tstr.value == 'tip':
            tags = ''
        else:
            tags = ' <%s>' % ','.join(tstr.value.split())
        return 'r%s%s%s' % (version, branch, tags)

    @property
    def release(self):
        """Retrieve the release information."""
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

