# Copyright 2016 Thomas Schatz, Xuan Nga Cao, Mathieu Bernard
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


class AbkhaziaSplit(AbstractCoreCommand):
    '''This class implements the 'abkhazia split' command'''
    name = 'split'
    description = 'split a corpus in train and test subcorpora'

    @classmethod
    def add_parser(cls, subparsers):
        # get basic parser init from AbstractCommand
        parser, _ = super(AbkhaziaSplit, cls).add_parser(subparsers)

        group = parser.add_argument_group('split arguments')

        prop = group.add_mutually_exclusive_group()
        default_prop = utils.config.get('split', 'default-test-proportion'),
        prop.add_argument(
            '-t', '--test-prop', type=float, metavar='<test>',
            default=None,
            help='''a float between 0.0 and 1.0, represent the proportion of the
            dataset to include in the test set. If not specfied, the
            value is automatically set to the complement of the
            <train>.  If <train> is not specified, <test> is set to
            {}'''.format(default_prop))

        prop.add_argument(
            '-T', '--train-prop', default=None, type=float, metavar='<train>',
            help='''a float between 0.0 and 1.0, represent the proportion of the
            dataset to include in the train set. If not specified, the
            value is automatically set to the complement of <test>''')

        group.add_argument(
            '-b', '--by-speakers', action='store_true',
            help='if specified, the data for each speaker is attributed '
            'either to the test or train subset as a whole. If not specified, '
            'data from a same speaker is randomly splited in the two subsets')

        group.add_argument(
            '-r', '--random-seed', default=None, type=int, metavar='<seed>',
            help='seed for pseudo-random numbers generation (default is to '
            'use the current system time). Use this option to compute a '
            'reproducible split')

        return parser

    @classmethod
    def run(cls, args):
        corpus_dir, output_dir = cls._parse_io_dirs(args)
        log = utils.logger.get_log(
            os.path.join(output_dir, 'split.log'), verbose=args.verbose)

        corpus = Corpus.load(corpus_dir, log=log)

        # retrieve the test proportion
        if args.train_prop is None:
            test_prop = (
                float(utils.config.get('split', 'default-test-proportion'))
                if args.test_prop is None else args.test_prop)
        else:
            test_prop = (
                1 - args.train_prop
                if args.test_prop is None else args.test_prop)

        train, test = corpus.split(
            train_prop=args.train_prop,
            test_prop=test_prop,
            by_speakers=args.by_speakers,
            random_seed=args.random_seed)

        train.save(os.path.join(output_dir, 'train', 'data'))
        test.save(os.path.join(output_dir, 'test', 'data'))
