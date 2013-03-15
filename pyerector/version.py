#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

HG_VERSION = '%hg.version%'
HG_BRANCH = '%hg.branch%'
HG_TAGS = '%hg.tags%'
RELEASE_PRODUCT = '%release.product%'
RELEASE_NUMBER = '%release.number%'

__all__ = [
    'get_version',
    'get_release',
]

def get_version():
    version = HG_VERSION.replace('+', '')
    branch = HG_BRANCH != 'default' and ' (%s)' % HG_BRANCH or ''
    tags = HG_TAGS != 'tip' and (' <%s>' % ','.join(HG_TAGS.split())) or ''
    return 'r%s%s%s' % (version, branch, tags)

def get_release():
    return '%s %s' % (RELEASE_PRODUCT, RELEASE_NUMBER)

