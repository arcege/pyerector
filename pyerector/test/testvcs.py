#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import os
import sys

from .base import *

PyVersionCheck()

from pyerector.variables import Variable
from pyerector.vcs import VCS, Git, Mercurial, Subversion
import pyerector

class TestVCS(TestCase):
    @classmethod
    def setUpClass(cls):
        notfound = {
            'win': ' is not recognized as an internal or external command',
            'lin': ' command not found',
            'mac': '',
            '': '',
        }
        super(TestVCS, cls).setUpClass()
        cls.nodir = os.path.join(cls.dir, 'novcs')
        cls.hgdir = os.path.join(cls.dir, 'mercurial')
        cls.gitdir = os.path.join(cls.dir, 'git')
        cls.svnadmdir = os.path.join(cls.dir, 'svnrepos')
        cls.svndir = os.path.join(cls.dir, 'subversion')
        # assume we have the tools
        cls.havehg = cls.havegit = cls.havesvn = True
        # checking Mercurial (hg)
        p = os.popen('hg init "%s"' % cls.hgdir, 'r')
        output = p.read()
        rc = p.close()
        if rc and cls.platform and output.find(notfound[cls.platform]) != -1:
            cls.havehg = False
        else:
            assert rc is None, \
                    'could not create mercurial repository: %s' % output
        # checking Git
        p = os.popen('git init "%s" 2>&1' % cls.gitdir, 'r')
        output = p.read()
        rc = p.close()
        if rc and cls.platform and output.find(notfound[cls.platform]) != -1:
            cls.havegit = False
        else:
            assert rc is None, \
                    'could not create git repository: %s' % output
        # checking Subversion (svn)
        p = os.popen('svnadmin create "%s"' % cls.svnadmdir, 'r')
        output = p.read()
        rc = p.close()
        if rc and cls.platform and output.find(notfound[cls.platform]) != -1:
            cls.havesvn = False
        else:
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
    def _tearDownClass(cls):
        userwritable = int('755', 8)
        for (name, dirnames, filenames) in os.walk(self.dir, topdown=False):
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
        self.lastdir = pyerector.vcs.basedir
    def tearDown(self):
        pyerector.vcs.basedir = self.lastdir
    def testvcs_check_novcs(self):
        # set to temp directory with no version control
        pyerector.vcs.basedir = self.nodir
        self.assertRaises(RuntimeError, VCS)
    def testvcs_check_mercurial(self):
        if self.havehg:
            pyerector.vcs.basedir = self.hgdir
            self.assertIsInstance(VCS(), Mercurial)
    def testvcs_check_git(self):
        if self.havegit:
            pyerector.vcs.basedir = self.gitdir
            self.assertIsInstance(VCS(), Git)
    def testvcs_check_subversion(self):
        if self.havesvn:
            pyerector.vcs.basedir = self.svndir
            self.assertIsInstance(VCS(), Subversion)
    def testvcs_info_mercurial(self):
        if self.havehg:
            pyerector.vcs.basedir = self.hgdir
            vcs = VCS(rootdir=self.hgdir)
            self.assertEqual(Variable('hg.version').value, '000000000000')
            self.assertEqual(Variable('hg.branch').value, 'default')
            self.assertEqual(Variable('hg.tags').value, 'tip')
    def testvcs_info_git(self):
        if self.havegit:
            pyerector.vcs.basedir = self.gitdir
            vcs = VCS(rootdir=self.gitdir)
            self.assertEqual(Variable('git.version').value, '')
            self.assertEqual(Variable('git.branch').value, '')
            self.assertEqual(Variable('git.tags').value, '')
    def testcvs_info_svn(self):
        if self.havesvn:
            pyerector.vcs.basedir = self.svndir
            vcs = VCS(rootdir=self.svndir)
            self.assertEqual(Variable('svn.version').value, '0')
            self.assertEqual(Variable('svn.branch').value, '')
            self.assertEqual(Variable('svn.tags').value, '')

