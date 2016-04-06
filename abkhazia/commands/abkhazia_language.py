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
"""Implementation of the 'abkhazia language' command"""

import argparse

import abkhazia.utils as utils
from abkhazia.commands.abstract_command import AbstractRecipeCommand
from abkhazia.kaldi.language_model import LanguageModel


class AbkhaziaLanguage(AbstractRecipeCommand):
    name = LanguageModel.name
    description = 'compute a n-gram language model from an abkhazia corpus'

    @classmethod
    def add_parser(cls, subparsers):
        parser, _ = super(AbkhaziaLanguage, cls).add_parser(subparsers)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter

        group = parser.add_argument_group('command options')

        group = parser.add_argument_group(
            'language model parameters', 'those parameters can also be '
            'specified in the [language] section of the configuration file')

        group.add_argument(
            '-s', '--optional-silence', action='store_true',
            help='do all computations if specified, else focus '
            'on the main ones')

        group.add_argument(
            '-w', '--word-position-dependent', action='store_true',
            help='''Should be set to true or false depending on whether the
            language model produced is destined to be used with an acoustic
            model trained with or without word position dependent
            variants of the phones. This option have no effect on word
            level models.''')

        group.add_argument(
            '-n', '--model-order', type=int, metavar='<N>',
            default=utils.config.get('language', 'model-order'),
            help='n in n-gram, must be a positive integer')

        group.add_argument(
            '-l', '--model-level',
            default=utils.config.get('language', 'model-level'),
            help="compute either a phone-level or a word-level language "
            "model, default is '%(default)s'",
            metavar='<phone|word>', choices=['phone', 'word'])

    @classmethod
    def run(cls, args):
        corpus, output_dir = cls.prepare_for_run(args)

        # retrieve recipe parameters
        if args.word_position_dependent is None:
            args.word_position_dependent = utils.config.get(
                'language', 'word-position-dependent')

        if args.model_order is None:
            args.model_order = utils.config.get('language', 'model-order')

        # instanciate the lm recipe creator
        recipe = LanguageModel(corpus, output_dir, args.verbose)
        recipe.order = args.model_order
        recipe.level = args.model_level
        recipe.position_dependent_phones = args.word_position_dependent
        recipe.silence_probability = 0.5 if args.optional_silence else 0.0

        # finally create and/or run the recipe
        if not args.only_run:
            recipe.create()
        if not args.no_run:
            recipe.run()
            recipe.export()
