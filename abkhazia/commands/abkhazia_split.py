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
# along with abkahzia. If not, see <http://www.gnu.org/licenses/>.
"""Implementation of the 'abkazia split' command"""

import argparse
import sys

import abkhazia.utils.split as split


class AbkhaziaSplit(object):
    '''This class implemnts the 'abkahzia split' command

    Basically this class defines an argument parser, parses the
    arguments and split a corpus in train and test subsets. The
    spliting operation is delegated to the split.SplitCorpus class.

    '''
    name = 'split'
    description = 'Split a corpus in train and test subsets'

    def __init__(self):
        # parse the arguments (ignore the first and second which are
        # 'abkahzia split')
        args = self.parser().parse_args(sys.argv[2:])

        # instanciate a SplitCorpus instance
        spliter = split.SplitCorpus(
            args.input_dir, args.output_dir, args.random_seed, args.verbose)

        # choose the split function according to --by-speakers
        split_fun = (spliter.split_by_speakers if args.by_speakers
                     else spliter.split)

        # split the corpus and write it to the output directory
        split_fun(args.test_prop, args.train_prop)

    @classmethod
    def parser(cls):
        """Return a parser for the split command"""
        parser = argparse.ArgumentParser(
            prog='abkhazia split',
            usage='%(prog)s <input-dir> [--output-dir OUTPUT_DIR]\n' +
            ' '*23 + ('\n' + ' '*23).join([
                '[--help] [--verbose] [--by-speakers] [--random-seed SEED]',
                '[--test-prop TEST|--train-prop TRAIN']),
            description=cls.description)

        group = parser.add_argument_group('directories')

        group.add_argument(
            'input_dir', metavar='input-dir',
            help='root directory of the abkhazia corpus to split')

        group.add_argument(
            '-o', '--output-dir', default=None,
            help='output directory of the splited corpus, '
            'if not specified use input-dir/split')

        parser.add_argument(
            '-v', '--verbose', action='store_true',
            help='display more messages to stdout')

        group = parser.add_argument_group('split arguments')

        group.add_argument(
            '-b', '--by-speakers', action='store_true',
            help='if specified, the data for each speaker is attributed '
            'either to the test or train subset as a whole. If not specified, '
            'data from a same speaker is randomly splitted in the two subsets')

        group.add_argument(
            '-r', '--random-seed', default=None, metavar='SEED',
            help='seed for pseudo-random numbers generation (default is to '
            'use the current system time)')

        prop = group.add_mutually_exclusive_group()
        prop.add_argument(
            '-t', '--test-prop', type=float, metavar='TEST',
            default=split.SplitCorpus.default_test_prop(),
            help='''a float between 0.0 and 1.0, represent the proportion of the
            dataset to include in the test set. If not specfied, the
            value is automatically set to the complement of the train
            size. If train size is not specified, test size is set to
            %(default)s.''')

        prop.add_argument(
            '-T', '--train-prop', default=None, type=float, metavar='TRAIN',
            help='''a float between 0.0 and 1.0, represent the proportion of the
            dataset to include in the train set. If not specified, the
            value is automatically set to the complement of the test
            size.''')

        return parser
