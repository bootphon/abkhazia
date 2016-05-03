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

from abkhazia.commands.abstract_command import AbstractRecipeCommand
import abkhazia.utils as utils
import abkhazia.utils.split as split


class AbkhaziaSplit(AbstractRecipeCommand):
    '''This class implements the 'abkhazia split' command'''
    name = 'split'
    description = 'split a corpus in train and test subsets'

    @classmethod
    def run(cls, args):
        corpus, output_dir = cls.prepare_for_run(args)

        # instanciate a SplitCorpus instance
        spliter = split.SplitCorpus(
            corpus, output_dir,
            args.random_seed, args.prune_lexicon, args.verbose)

        # choose the split function according to --by-speakers
        split_fun = (spliter.split_by_speakers if args.by_speakers
                     else spliter.split)

        # retrieve the test proportion
        if args.train_prop is None:
            test_prop = (
                float(utils.config.get('split', 'default-test-proportion'))
                if args.test_prop is None else args.test_prop)
        else:
            test_prop = (
                1 - args.train_prop
                if args.test_prop is None else args.test_prop)

        # split the corpus and write it to the output directory
        split_fun(test_prop, args.train_prop)

        if args.with_validation:
            spliter.validate()

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
            '-p', '--prune-lexicon', action='store_true',
            help='''if specified, remove from the lexicon all words that are not
            present at least once in the training set. This have
            effect on word-level language models. Could be useful when
            using a lexicon that is tailored to the corpus to the
            point of overfitting (i.e. only words occuring in the
            corpus were included and many other common words weren't),
            which could lead to overestimated performance on words
            from the lexicon appearing in the test only.''')

        group.add_argument(
            '-r', '--random-seed', default=None, type=int, metavar='<seed>',
            help='seed for pseudo-random numbers generation (default is to '
            'use the current system time). Use this option to compute a '
            'reproducible split')

        parser.add_argument(
            '--with-validation', action='store_true',
            help='if specified, check the created train and test '
            'subsets are valid abkhazia corpora')

        return parser
