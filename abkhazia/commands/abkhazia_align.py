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

from abkhazia.commands.abstract_command import AbstractRecipeCommand
import abkhazia.kaldi.force_align as force_align


class AbkhaziaAlign(AbstractRecipeCommand):
    '''This class implements the 'abkhazia align' command'''
    name = 'align'
    description = 'compute forced-aligment'

    @classmethod
    def run(cls, args):
        corpus, output_dir = cls.prepare_for_run(args)

        # get back the language model directory TODO this code is
        # shared with train, factorize!
        lang = (corpus if args.language_model is None
                else os.path.abspath(args.language_model))
        lang += '/language/s5/data/language'

        # ensure it's a directory and we have both oov.int and
        # G.fst in it
        if not os.path.isdir(lang):
            raise IOError(
                'language model not found: {}.\n'.format(lang) +
                "Please provide a language model "
                "(use 'abkhazia language <args>')")

        if not (os.path.isfile(os.path.join(lang, 'oov.int')) and
                os.path.isfile(os.path.join(lang, 'G.fst'))):
            raise IOError('not a valid language model directory: {}'
                          .format(lang))

        # get back the acoustic model directory
        acoustic = (corpus if args.acoustic_model is None
                    else os.path.abspath(args.acoustic_model))
        acoustic += '/train/s5/exp/acoustic_model'

        # ensure it's a directory and we have final.mdl in it
        if not os.path.isdir(lang):
            raise IOError(
                'acoustic model not found: {}.\n'.format(lang) +
                "Please provide a trained acoustic model "
                "(use 'abkhazia train <args>')")

        if not os.path.isfile(os.path.join(acoustic, 'final.mdl')):
            raise IOError('not a valid acoustic model directory: {}'
                          .format(acoustic))

        # this is used to configure the force_align.sh.in script in
        # create()
        del args.language_model
        del args.acoustic_model
        args.lang = lang
        args.acoustic = acoustic

        # instanciate the kaldi recipe creator
        recipe = force_align.ForceAlign(corpus, output_dir, args.verbose)

        # finally create and/or run the recipe
        if not args.only_run:
            recipe.create(args)
        if not args.no_run:
            recipe.run()
            recipe.export()

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

        dir_group.add_argument(
            '-l', '--language-model', metavar='<lm-dir>', default=None,
            help='''the language model recipe directory, data is read from
            <lm-dir>/language. If not specified, use <lm-dir>=<corpus>.''')

        dir_group.add_argument(
            '-a', '--acoustic-model', metavar='<am-dir>', default=None,
            help='''the acoustic model recipe directory, data is read from
            <am-dir>/train. If not specified, use <am-dir>=<corpus>.''')

        return parser
