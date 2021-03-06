#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.

import os
import time

try:
    from .base import *
except ValueError:
    import sys
    sys.path.insert(
        0,
        os.path.normpath(
            os.path.join(
                os.path.dirname(__file__), os.pardir, os.pardir
            )
        )
    )
    from base import *

PyVersionCheck()

from pyerector.path import Path
from pyerector.variables import Variable
from pyerector.vcs import VCS, load_plugins
from pyerector.variables import V


class TestVCS(TestCase):
    @classmethod
    def setUpClass(cls):
        notfound = {
            'win': ' is not recognized as an internal or external command',
            'lin': ' command not found',
            'mac': '',
            '': '',
        }
        load_plugins()
        super(TestVCS, cls).setUpClass()
        cls.nodir = cls.dir + 'novcs'
        cls.hgdir = cls.dir + 'mercurial'
        cls.gitdir = cls.dir + 'git'
        cls.svnadmdir = cls.dir + 'svnrepos'
        cls.svndir = cls.dir + 'subversion'
        # assume we have the tools
        cls.havehg = cls.havegit = cls.havesvn = True
        # checking Mercurial (hg)
        p = os.popen('hg init "%s"' % cls.hgdir, 'r')
        output = p.read()
        rc = p.close()
        if rc and cls.platform and output.find(notfound[cls.platform]) != -1:
            cls.havehg = False
            logger.info('TestVCS: no mercurial')
        else:
            logger.debug('TestVCS: mercurial initialized')
            assert rc is None, \
                'could not create mercurial repository: %s' % output
        # checking Git
        p = os.popen('git init "%s" 2>&1' % cls.gitdir, 'r')
        output = p.read()
        rc = p.close()
        if rc and cls.platform and output.find(notfound[cls.platform]) != -1:
            cls.havegit = False
            logger.info('TestVCS: no git')
        else:
            logger.debug('TestVCS: git initialized')
            assert rc is None, \
                'could not create git repository: %s' % output
        # checking Subversion (svn)
        cls.when = time.strftime('%Y-%m-%d %T %z (%a, %d %b %Y)')
        p = os.popen('svnadmin create "%s"' % cls.svnadmdir, 'r')
        output = p.read()
        rc = p.close()
        if rc and cls.platform and output.find(notfound[cls.platform]) != -1:
            cls.havesvn = False
            logger.info('TestVCS: no subversion')
        else:
            logger.debug('TestVCS: subversion initialized')
            assert rc is None, \
                'could not create subversion repository: %s' % output
        if cls.havesvn:
            p = os.popen('svn co "file://%s" "%s"' % (cls.svnadmdir, cls.svndir),
                         'r')
            output = p.read()
            rc = p.close()
            if rc:
                cls.havesvn = False
            #assert rc is None, \
            #        '(%s) could not create svn working copy: %s' % (rc, output)

    @classmethod
    def _tearDownClass(cls):
        userwritable = int('755', 8)
        for (name, dirnames, filenames) in os.walk(cls.dir, topdown=False):
            for fn in filenames:
                path = os.path.join(name, fn)
                os.chmod(path, userwritable)
                os.remove(path)
            # we should have gotten rid of the children first
            for fn in dirnames:
                path = os.path.join(name, fn)
                os.chmod(path, userwritable)
                os.rmdir(path)

    def setUp(self):
        self.lastdir = V['basedir']

    def tearDown(self):
        V['basedir'] = self.lastdir

    def testvcs_check_novcs(self):
        # set to temp directory with no version control
        V['basedir'] = Path(self.nodir)
        vcs = VCS()
        self.assertEqual(vcs.name, 'none')
        self.assertIsNone(vcs.directory)

    def testvcs_check_mercurial(self):
        if self.havehg:
            V['basedir'] = Path(self.hgdir)
            self.assertEqual(VCS().name, 'mercurial')

    def testvcs_check_git(self):
        if self.havegit:
            V['basedir'] = Path(self.gitdir)
            self.assertEqual(VCS().name, 'git')

    def _testvcs_check_subversion(self):
        if self.havesvn:
            V['basedir'] = Path(self.svndir)
            self.assertEqual(VCS().name, 'subversion')

    def testvcs_info_mercurial(self):
        if self.havehg:
            V['basedir'] = Path(self.hgdir)
            VCS(rootdir=self.hgdir)
            self.assertEqual(Variable('hg.version').value, '000000000000')
            self.assertEqual(Variable('hg.branch').value, 'default')
            self.assertEqual(Variable('hg.tags').value, 'tip')
            self.assertEqual(Variable('hg.user').value, '')
            self.assertEqual(Variable('hg.date').value,
                             '1970-01-01 00:00 +0000')

    def testvcs_info_git(self):
        if self.havegit:
            V['basedir'] = Path(self.gitdir)
            VCS(rootdir=self.gitdir)
            self.assertEqual(Variable('git.version').value, '')
            self.assertEqual(Variable('git.branch').value, '')
            self.assertEqual(Variable('git.tags').value, '')
            self.assertEqual(Variable('git.user').value, '')
            self.assertEqual(Variable('git.date').value, '')

    def testcvs_info_svn(self):
        if self.havesvn:
            # string format used by SVN
            V['basedir'] = Path(self.svndir)
            VCS(rootdir=self.svndir)
            self.assertEqual(Variable('svn.version').value, '0')
            self.assertEqual(Variable('svn.branch').value, '')
            self.assertEqual(Variable('svn.tags').value, '')
            self.assertEqual(Variable('svn.user').value, '')
            # can't get the date to sync between "now" and svnadmin init
            #self.assertEqual(Variable('svn.date').value, self.when)


