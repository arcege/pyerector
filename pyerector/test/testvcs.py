#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import os

from .base import PyVersionCheck, TestCase

PyVersionCheck()

from pyerector.variables import Variable
from pyerector.vcs import VCS, Git, Mercurial, Subversion
import pyerector

class TestVCS(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestVCS, cls).setUpClass()
        cls.nodir = os.path.join(cls.dir, 'novcs')
        cls.hgdir = os.path.join(cls.dir, 'mercurial')
        cls.gitdir = os.path.join(cls.dir, 'git')
        cls.svnadmdir = os.path.join(cls.dir, 'svnrepos')
        cls.svndir = os.path.join(cls.dir, 'subversion')
        p = os.popen('hg init %s' % cls.hgdir, 'r')
        assert p.close() is None, "could not create mercurial repository"
        p = os.popen('git init %s' % cls.gitdir, 'r')
        assert p.close() is None, "could not create git repository"
        p = os.popen('svnadmin create %s' % cls.svnadmdir, 'r')
        assert p.close() is None, "could not create subversion repository"
        p = os.popen('svn co file://%s %s' % (cls.svnadmdir, cls.svndir), 'r')
        assert p.close() is None, "could not create svn working copy"
    def setUp(self):
        self.lastdir = pyerector.vcs.basedir
    def tearDown(self):
        pyerector.vcs.basedir = self.lastdir
    def testvcs_check_novcs(self):
        # set to temp directory with no version control
        pyerector.vcs.basedir = self.nodir
        self.assertRaises(RuntimeError, VCS)
    def testvcs_check_mercurial(self):
        pyerector.vcs.basedir = self.hgdir
        self.assertIsInstance(VCS(), Mercurial)
    def testvcs_check_git(self):
        pyerector.vcs.basedir = self.gitdir
        self.assertIsInstance(VCS(), Git)
    def testvcs_check_subversion(self):
        pyerector.vcs.basedir = self.svndir
        self.assertIsInstance(VCS(), Subversion)
    def testvcs_info_mercurial(self):
        pyerector.vcs.basedir = self.hgdir
        vcs = VCS(rootdir=self.hgdir)
        self.assertEqual(Variable('hg.version').value, '000000000000')
        self.assertEqual(Variable('hg.branch').value, 'default')
        self.assertEqual(Variable('hg.tags').value, 'tip')
    def testvcs_info_git(self):
        pyerector.vcs.basedir = self.gitdir
        vcs = VCS(rootdir=self.gitdir)
        self.assertEqual(Variable('git.version').value, '')
        self.assertEqual(Variable('git.branch').value, '')
        self.assertEqual(Variable('git.tags').value, '')
    def testcvs_info_svn(self):
        pyerector.vcs.basedir = self.svndir
        vcs = VCS(rootdir=self.svndir)
        self.assertEqual(Variable('svn.version').value, '0')
        self.assertEqual(Variable('svn.branch').value, '')
        self.assertEqual(Variable('svn.tags').value, '')

