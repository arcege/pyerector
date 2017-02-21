#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.
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

    def __str__(self):
        return '%s %s' % (self.release, self.version)

    def __repr__(self):
        return '<VersionClass "%s" "%s" "%s" "%s" "%s">' % (
            V['pyerector.release.product'],
            V['pyerector.release.number'],
            V['pyerector.release.tags'],
            V['pyerector.release.version'],
            V['pyerector.release.branch'],
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

    def __call__(self, *args):
        from logging import getLogger
        logger = getLogger('pyerector')
        name = V['pyerector.release.product']
        number = V['pyerector.release.number']
        for desired in args:
            if desired and '%s %s' % (name, desired) > self.release:
                logger.error(
                    'Version: %s %s does not match desired %s, aborting',
                    name, number, desired)
                raise SystemExit(1)

HG_VERSION = '%hg.version%'
HG_BRANCH = '%hg.branch%'
HG_TAGS = '%hg.tags%'
RELEASE_PRODUCT = '%release.product%'
RELEASE_NUMBER = '%release.number%'

__all__ = [
    'Version',
]

Version = VersionClass()

