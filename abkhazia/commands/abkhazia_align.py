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
"""Implementation of the 'abkhazia align' command"""

import argparse
import os

from abkhazia.commands.abstract_command import AbstractKaldiCommand
import abkhazia.core.force_align as force_align


class AbkhaziaAlign(AbstractKaldiCommand):
    '''This class implements the 'abkhazia align' command'''
    name = 'align'
    description = 'compute forced-aligment'

    @staticmethod
    def long_description():
        """Return the docstring of the ForceAlign class"""
        return force_align.ForceAlign.__doc__.replace(' '*4, ' '*2).strip()

    @classmethod
    def add_parser(cls, subparsers):
        """Return a parser for the align command"""
        # get basic parser init from AbstractCommand
        parser, dir_group = super(AbkhaziaAlign, cls).add_parser(subparsers)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.description = cls.long_description()

        parser.add_argument(
            '--no-words', action='store_true',
            help='do not write words in the final alignment file, only phones')

        dir_group.add_argument(
            '-l', '--language-model', metavar='<lm-dir>', default=None,
            help='''the language model recipe directory, data is read from
            <lm-dir>/language. If not specified, use <lm-dir>=<corpus>.''')

        dir_group.add_argument(
            '-f', '--features', metavar='<feat-dir>', default=None,
            help='''the features directory, data is read from
            <feat-dir>/features/mfcc. If not specified, use
            <feat-dir>=<corpus>.''')

        dir_group.add_argument(
            '-a', '--acoustic-model', metavar='<am-dir>', default=None,
            help='''the acoustic model recipe directory, data is read from
            <am-dir>/acoustic. If not specified, use <am-dir>=<corpus>.''')

        return parser

    @classmethod
    def run(cls, args):
        corpus, output_dir = cls._parse_io_dirs(args)

        # get back the language model directory
        lang = (corpus if args.language_model is None
                else os.path.abspath(args.language_model))
        lang += '/language'

        # get back the acoustic model directory
        acoustic = (corpus if args.acoustic_model is None
                    else os.path.abspath(args.acoustic_model))
        acoustic += '/acoustic'

        # get back the features directory
        feat = (corpus if args.features is None
                else os.path.abspath(args.features))
        feat += '/features'

        # instanciate the kaldi recipe creator
        recipe = force_align.ForceAlign(corpus, output_dir, args.verbose)
        recipe.njobs = args.njobs
        recipe.lm_dir = lang
        recipe.feat_dir = feat
        recipe.am_dir = acoustic
        recipe.delete_recipe = False if args.recipe else True

        # finally compute the alignments
        recipe.create()
        recipe.run()
        recipe.export(not args.no_words)
