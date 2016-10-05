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
"""Implementation of the 'abkhazia language' command"""

import argparse
import os

import abkhazia.utils as utils
from abkhazia.commands.abstract_command import AbstractKaldiCommand
from abkhazia.models.language_model import LanguageModel
from abkhazia.corpus import Corpus


class AbkhaziaLanguage(AbstractKaldiCommand):
    name = LanguageModel.name
    description = 'compute a n-gram language model on a corpus'

    @classmethod
    def add_parser(cls, subparsers):
        parser, _ = super(AbkhaziaLanguage, cls).add_parser(subparsers)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter

        group = parser.add_argument_group('command options')

        group = parser.add_argument_group(
            'language model parameters', 'those parameters can also be '
            'specified in the [language] section of the configuration file')

        group.add_argument(
            '-s', '--no-silence', action='store_true',
            help='do not model silences (probability of 0, '
            'default is a silence probability of 0.5)')

        group.add_argument(
            '-w', '--word-position-dependent', action='store_true',
            help='''Should be set to true or false depending on whether the
            language model produced is destined to be used with an acoustic
            model trained with or without word position dependent
            variants of the phones.''')

        group.add_argument(
            '-n', '--model-order', type=int, metavar='<N>',
            default=utils.config.get('language', 'model-order'),
            help='n in n-gram, must be a positive integer, '
            'default is %(default)s')

        group.add_argument(
            '-l', '--model-level',
            default=utils.config.get('language', 'model-level'),
            help="compute either a phone-level or a word-level language "
            "model, default is '%(default)s'",
            metavar='<phone|word>', choices=['phone', 'word'])

    @classmethod
    def run(cls, args):
        corpus_dir, output_dir = cls._parse_io_dirs(args)
        log = utils.logger.get_log(
            os.path.join(output_dir, 'language.log'), verbose=args.verbose)

        # retrieve recipe parameters, if not specified in the command
        # read them from the configuration file
        if args.word_position_dependent is None:
            args.word_position_dependent = utils.config.get(
                'language', 'word-position-dependent')

        if args.model_order is None:
            args.model_order = utils.config.get('language', 'model-order')

        corpus = Corpus.load(corpus_dir, validate=args.validate, log=log)

        # instanciate the lm recipe creator
        recipe = LanguageModel(corpus, output_dir, log=log)
        recipe.order = args.model_order
        recipe.level = args.model_level
        recipe.position_dependent_phones = args.word_position_dependent
        recipe.silence_probability = 0.0 if args.no_silence else 0.5
        recipe.delete_recipe = False if args.recipe else True

        # finally create and/or run the recipe
        recipe.create()
        recipe.run()
        recipe.export()
