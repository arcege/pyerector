#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.
"""Mercurial(hg) based version control hooks."""

import os

from ..helper import Subcommand
from .base import DVCS_Base
from ..variables import Variable

__all__ = [
    'Mercurial'
]


class Mercurial(DVCS_Base):
    """Version control class for Mercurial."""
    name = 'mercurial'
    prog = 'hg'
    directory = '.hg'

    def current_info(self):
        """Retrieve information from the workarea."""
        import logging
        proc = Subcommand(
            (self.prog, 'identify', '--id'),
            wait=True,
            wdir=self.rootdir,
            stdout=Subcommand.PIPE,
            stderr=os.devnull,
        )
        hgid = proc.stdout.read().decode('UTF-8').strip()
        logging.debug('hgid = %s', hgid)
        if proc.returncode != 0:
            raise RuntimeError('could not retrieve Mercurial node')
        del proc
        proc = Subcommand(
            (self.prog, 'log', '-r', hgid.replace('+', ''), '--template',
             '{node|short}\n{author|email}\n{date|isodate}\n{branch}\n{tags}\n'
            ),
            wait=True,
            wdir=self.rootdir,
            stdout=Subcommand.PIPE,
            stderr=os.devnull,
        )
        hgout = proc.stdout.read().decode('UTF-8')
        logging.debug('hgout = %s', repr(hgout))
        if proc.returncode == 0:
            parts = hgout.rstrip().split('\n')
            logging.info('parts = %s', parts)
            try:
                parts[3]
            except IndexError:
                parts.append(None)
            try:
                parts[4]
            except IndexError:
                parts.append(None)
            Variable('hg.version', parts[0])
            Variable('hg.user', parts[1])
            Variable('hg.date', parts[2])
            Variable('hg.branch', parts[3])
            Variable('hg.tags', parts[4])

Mercurial.register()

