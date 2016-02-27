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

import os
import shutil

from abkhazia.commands.abstract_command import AbstractCommand
import abkhazia.utils as utils
import abkhazia.utils.split as split


class AbkhaziaSplit(AbstractCommand):
    '''This class implements the 'abkahzia split' command'''
    name = 'split'
    description = 'split a corpus in train and test subsets'

    @classmethod
    def run(cls, args):
        # retrieve the corpus input directory
        if args.corpus.startswith(('/', './', '../', '~/')):
            corpus = args.corpus
        else:
            corpus = os.path.join(
                utils.config.get('abkhazia', 'data-directory'),
                args.corpus)

        # retrieve the output directory
        output_dir = corpus if args.output_dir is None else args.output_dir

        # if --force, remove any existing output_dir/split
        if args.force:
            split_dir = os.path.join(output_dir, 'split')
            if os.path.exists(split_dir):
                print 'removing {}'.format(split_dir)
                shutil.rmtree(split_dir)

        # instanciate a SplitCorpus instance
        spliter = split.SplitCorpus(
            corpus, output_dir, args.random_seed, args.verbose)

        # choose the split function according to --by-speakers
        split_fun = (spliter.split_by_speakers if args.by_speakers
                     else spliter.split)

        # split the corpus and write it to the output directory
        split_fun(args.test_prop, args.train_prop)


    @classmethod
    def add_parser(cls, subparsers):
        # get basic parser init from AbstractCommand
        parser = super(AbkhaziaSplit, cls).add_parser(subparsers)

        parser.add_argument(
            '-v', '--verbose', action='store_true',
            help='display more messages to stdout')

        parser.add_argument(
            '-f', '--force', action='store_true',
            help='if specified, overwrite the result directory '
            '<output-dir>/split. If not specified but the directory exists, '
            'the program fails.')

        group = parser.add_argument_group('directories')

        group.add_argument(
            'corpus', metavar='<corpus>',
            help="""
            the input abkhazia corpus to split. Must be a directory
            either relative to the abkhazia data directory ({0}) or
            relative/absolute on the filesystem. The following rule
            applies: if <corpus> starts with './' , '../' or '/', path is
            guessed directly, else <corpus> is guessed as a subdir in
            {0}""".format(utils.config.get('abkhazia', 'data-directory')))

        group.add_argument(
            '-o', '--output-dir', default=None, metavar='<output-dir>',
            help='output directory, the splited corpus is created in '
            '<output-dir>/split. '
            'If not specified use <output-dir> = <corpus>.')

        group = parser.add_argument_group('split arguments')

        prop = group.add_mutually_exclusive_group()
        prop.add_argument(
            '-t', '--test-prop', type=float, metavar='<test>',
            default=split.SplitCorpus.default_test_prop(),
            help='''a float between 0.0 and 1.0, represent the proportion of the
            dataset to include in the test set. If not specfied, the
            value is automatically set to the complement of the
            <train>.  If <train> is not specified, <test> is set to
            %(default)s.''')

        prop.add_argument(
            '-T', '--train-prop', default=None, type=float, metavar='<train>',
            help='''a float between 0.0 and 1.0, represent the proportion of the
            dataset to include in the train set. If not specified, the
            value is automatically set to the complement of <test>.''')

        group.add_argument(
            '-b', '--by-speakers', action='store_true',
            help='if specified, the data for each speaker is attributed '
            'either to the test or train subset as a whole. If not specified, '
            'data from a same speaker is randomly splited in the two subsets')

        group.add_argument(
            '-r', '--random-seed', default=None, metavar='<seed>',
            help='seed for pseudo-random numbers generation (default is to '
            'use the current system time). Use this option to compute a '
            'reproducible split.')

        return parser
