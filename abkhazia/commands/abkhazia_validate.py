# Copyright 2016 Thomas Schatz, Xuan-Nga Cao, Mathieu Bernard
#
# This file is part of abkhazia: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Abkhazia is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with abkhazia. If not, see <http://www.gnu.org/licenses/>.
"""Implementation of the 'abkazia validate' command"""

import argparse
import logging
import os
import sys
import textwrap

from abkhazia.commands.abstract_command import AbstractCommand
from abkhazia.corpus import Corpus
import abkhazia.utils as utils


class AbkhaziaValidate(AbstractCommand):
    """This class implements the 'abkhazia validate' command"""
    name = 'validate'
    description = 'validate a corpus read from disk'

    @classmethod
    def add_parser(cls, subparsers, name=None):
        """Add the command's parser to the `subparsers`

        This method implements only minimal parsing and should be
        overloaded in child classes. Basically you may want to add
        some parameters and options to your command.

        If name is None, take cls.name

        """
        if name is None:
            name = cls.name

        # add a new subparser for the command
        parser = subparsers.add_parser(name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter

        # link args.command to the run() method
        parser.set_defaults(command=cls.run)

        # add a brief description of the command
        parser.description = textwrap.dedent(cls.description)

        parser.add_argument(
            'corpus', metavar='<corpus>',
            help='Directory where the corpus to validate is stored.')

        return parser

    @staticmethod
    def _parse_corpus_dir(corpus):
        """Parse the corpus input directory as specified in help message

        If `corpus` doesn't start with './' , '../', '~/' or '/', the
        following rule applies: `corpus` is guessed as a subdirectory
        of 'abkhazia.data-directory' from config file and, if not
        found, as a subdirectory of the current working directory.

        """
        if not corpus.startswith(('/', '.', '../', '~/')):
            # try to find the corpus in abkhazia data directory
            _corpus = os.path.join(
                utils.config.get('abkhazia', 'data-directory'), corpus)
            if os.path.isdir(_corpus):
                corpus = _corpus
        return os.path.abspath(corpus)

    @classmethod
    def run(cls, args):
        corpus_dir = cls._parse_corpus_dir(args.corpus)

        log = utils.logger.get_log(verbose=True)
        corpus = Corpus.load(corpus_dir, validate=False, log=log)

        if corpus.is_valid():
            log.info('corpus is valid')
            sys.exit(0)
        else:
            log.error('corpus is NOT valid')
            sys.exit(1)
