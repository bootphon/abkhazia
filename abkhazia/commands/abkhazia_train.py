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
"""Implementation of the 'abkhazia train' command"""

import argparse
import os

from abkhazia.commands.abstract_command import AbstractRecipeCommand
from abkhazia.kaldi.abkhazia2kaldi import add_argument
import abkhazia.kaldi.train as train


class AbkhaziaTrain(AbstractRecipeCommand):
    """This class implements the 'abkhazia train' command"""
    name = 'train'
    description = 'train (or retrain) an acoustic model'

    @classmethod
    def run(cls, args):
        corpus, output_dir = cls.prepare_for_run(args)

        # language model stuff
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

        # this is used to configure the train.sh.in script in create()
        del args.language_model
        args.lang = lang

        # instanciate the kaldi recipe creator
        recipe = train.AcousticModel(corpus, output_dir, args.verbose)

        # finally create and/or run the recipe
        if not args.only_run:
            recipe.create(args)
        if not args.no_run:
            recipe.run()

    @staticmethod
    def long_description():
        """Return the docstring of the ForceAlign class"""
        return train.AcousticModel.__doc__.replace(' '*4, ' '*2).strip()

    @classmethod
    def add_parser(cls, subparsers):
        """Return a parser for the align command"""
        # get basic parser init from AbstractCommand
        parser, dir_group = super(AbkhaziaTrain, cls).add_parser(subparsers)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.description = cls.long_description()

        dir_group.add_argument(
            '-l', '--language-model', metavar='<lm-dir>', default=None,
            help='''the language model recipe directory, data is read from
            <lm-dir>/language. If that option is not specified, take
            <lm-dir>=<corpus>.''')

        group = parser.add_argument_group(
            'acoustic model parameters', 'those parameters can also be '
            'specified in the [train] section of the configuration file')

        # TODO merge this option with the num-gauss/num-states options below
        group.add_argument(
            '-t',  '--type', metavar='<model-type>', default='tri',
            choices=['mono', 'tri', 'tri-sa', 'nnet'],
            help="""the type of acoustic model to train, choose <model-type> in 'mono'
            for monophone, 'tri' for triphone, 'tri-sa' for
            speaker-adapted triphone and 'nnet' for deep neural
            network""")

        def add_arg(name, type, help):
            add_argument(group, cls.name, name, type, help)

        add_arg('use-pitch', bool, 'MFCC features parameter')

        add_arg('num-states-si', int, 'number of states in the '
                'speaker-independent triphone model')

        add_arg('num-gauss-si', int, 'number of Gaussians in the '
                'speaker-independent triphone model')

        add_arg('num-states-sa', int, 'number of states in the '
                'speaker-adaptive triphone model')

        add_arg('num-gauss-sa', int, 'number of Gaussians in the '
                'speaker-adaptive triphone model')

        return parser
