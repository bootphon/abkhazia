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
    description = 'compute a language model'

    @classmethod
    def add_parser(cls, subparsers):
        parser, _ = super(AbkhaziaLanguage, cls).add_parser(subparsers)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter

        group = parser.add_argument_group('command options')

        group = parser.add_argument_group(
            'language model parameters', 'those parameters can also be '
            'specified in the [language] section of the configuration file')

        from abkhazia.kaldi.abkhazia2kaldi import add_argument

        def add_arg(name, type, help, metavar=None, choices=None):
            add_argument(group, cls.name, name, type, help, metavar, choices)

        add_arg(
            'optional-silence', bool,
            'do all computations if true, else focus on the main ones')

        add_arg(
            'word-position-dependent', bool,
            '''Should be set to true or false depending on whether the language
            model produced is destined to be used with an acoustic
            model trained with or without word position dependent
            variants of the phones''')

        add_arg(
            'model-order', int,
            'n in n-gram, only used if a LM is to be estimated from some '
            'text, see share/kaldi_templates/prepare_lm.sh.in')

        add_arg(
            'model-level', str,
            "compute either a phone-level or a word-level language model",
            metavar='<phone|word>', choices=['phone', 'word'])

    @classmethod
    def run(cls, args):
        corpus, output_dir = cls.prepare_for_run(args)

        # instanciate the lm recipe creator
        recipe = LanguageModel(corpus, output_dir, args.verbose)

        # retrieve recipe parameters
        if args.word_position_dependent is None:
            args.word_position_dependent = utils.config.get(
                'language', 'word-position-dependent')

        if args.model_order is None:
            args.model_order = utils.config.get('language', 'model-order')

        # finally create and/or run the recipe
        if not args.only_run:
            recipe.create(args)
        if not args.no_run:
            recipe.run()
            recipe.export()
