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
"""Implementation of the 'abkazia split' command"""

import os

from abkhazia.commands.abstract_command import AbstractCoreCommand
from abkhazia.corpus import Corpus
import abkhazia.utils as utils


class AbkhaziaSplitChallenge(AbstractCoreCommand):
    '''This class implements the 'abkhazia splitChallenge' command'''
    name = 'splitChallenge'
    description = 'split a corpus in train and test subcorpora'

    @classmethod
    def add_parser(cls, subparsers):
        # get basic parser init from AbstractCommand
        parser, _ = super(AbkhaziaSplitChallenge, cls).add_parser(subparsers)

        group = parser.add_argument_group('split arguments')

        prop = group.add_mutually_exclusive_group()
        prop.add_argument(
            '-n', '--new_speakers', type=int, metavar='<test>',
            default=5,
            help=''' an int, represents the number of 'new' speakers that will
            appear in the test set and won't be present at all in the 
            training set''')

        prop.add_argument(
            '-t', '--test_dur', default=10, type=float, metavar='<train>',
            help='''a float, represents the time of speech we want for 
            each speaker in the test set''')

        return parser

    @classmethod
    def run(cls, args):
        corpus_dir, output_dir = cls._parse_io_dirs(args)
        log = utils.logger.get_log(
            os.path.join(output_dir, 'split.log'), verbose=args.verbose)

        corpus = Corpus.load(corpus_dir, validate=args.validate, log=log)

        # retrieve the test proportion
        train, test = corpus.splitChallenge(nb_new_speaker=5,test_dur=10)

        train.save(os.path.join(output_dir, 'train', 'data'))
        test.save(os.path.join(output_dir, 'test', 'data'),copy_wavs=False)
