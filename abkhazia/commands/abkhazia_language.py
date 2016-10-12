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

        group = parser.add_argument_group('language model parameters')

        group.add_argument(
            '-s', '--silence-probability', default=0.5,
            metavar='<float>', type=float,
            help='usually 0.0 or 0.5, default is %(default)s'
            'default is a silence probability of 0.5)')

        group.add_argument(
            '-w', '--word-position-dependent', action='store_true',
            help='''Should be set to true or false depending on whether the
            language model produced is destined to be used with an acoustic
            model trained with or without word position dependent
            variants of the phones.''')

        group.add_argument(
            '-n', '--model-order', type=int, metavar='<int>', default=2,
            help='n in n-gram, must be a positive integer, '
            'default is %(default)s')

        group.add_argument(
            '-l', '--model-level', default='word',
            help="compute either a phone-level or a word-level language "
            "model, default is '%(default)s'",
            metavar='<phone|word>', choices=['phone', 'word'])

    @classmethod
    def run(cls, args):
        corpus_dir, output_dir = cls._parse_io_dirs(args)
        log = utils.logger.get_log(
            os.path.join(output_dir, 'language.log'), verbose=args.verbose)

        corpus = Corpus.load(corpus_dir, validate=args.validate, log=log)

        # instanciate the lm recipe and compute
        recipe = LanguageModel(
            corpus, output_dir, log=log,
            order=args.model_order, level=args.model_level,
            position_dependent_phones=args.word_position_dependent,
            silence_probability=args.silence_probability)
        recipe.delete_recipe = False if args.recipe else True
        recipe.compute()
