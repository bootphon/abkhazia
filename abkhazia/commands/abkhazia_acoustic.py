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
"""Implementation of the 'abkhazia acoustic' command"""

import argparse
import os

from abkhazia.commands.abstract_command import AbstractRecipeCommand
from abkhazia.kaldi.abkhazia2kaldi import add_argument
import abkhazia.kaldi.acoustic_model as acoustic_model


class AbkhaziaAcoustic(AbstractRecipeCommand):
    """This class implements the 'abkhazia acoustic' command"""
    name = 'acoustic'
    description = 'train (or retrain) an acoustic model'

    @classmethod
    def run(cls, args):
        # TODO nnet not supported
        if args.type == 'nnet':
            raise NotImplementedError(
                'neural network acoustic modeling not yet implemented')

        corpus, output_dir = cls.prepare_for_run(args)

        # get back the language model directory
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

        # used to configure the acoustic_model.sh.in script in
        # the create() method
        del args.language_model
        args.lang = lang

        # instanciate the kaldi recipe creator
        recipe = acoustic_model.AcousticModel(corpus, output_dir, args.verbose)

        # finally create and/or run the recipe
        if not args.only_run:
            recipe.create(args)
        if not args.no_run:
            recipe.run()

    @staticmethod
    def long_description():
        """Return the docstring of the AcousticModel class"""
        return acoustic_model.AcousticModel\
                             .__doc__.replace(' '*4, ' '*2).strip()

    @classmethod
    def add_parser(cls, subparsers):
        """Return a parser for the align command"""
        # get basic parser init from AbstractCommand
        parser, dir_group = super(AbkhaziaAcoustic, cls).add_parser(subparsers)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.description = cls.long_description()

        dir_group.add_argument(
            '-l', '--language-model', metavar='<lm-dir>', default=None,
            help='''the language model recipe directory, data is read from
            <lm-dir>/language. If not specified, use <lm-dir>=<corpus>.''')

        group = parser.add_argument_group(
            'acoustic model parameters', 'those parameters can also be '
            'specified in the [acoustic] section of the configuration file')

        # TODO merge this option with the num-gauss/num-states options below
        group.add_argument(
            '-t',  '--type', metavar='<model-type>', default='tri-sa',
            choices=['mono', 'tri', 'tri-sa', 'nnet'],
            help="""the type of acoustic model to train, choose <model-type> in 'mono'
            for monophone, 'tri' for triphone, 'tri-sa' for
            speaker-adapted triphone and 'nnet' for deep neural
            network. Default is '%(default)s'.""")

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

        group.add_argument(
            '-j', '--njobs-train', type=int, default=8, metavar='<njobs>',
            help="""number of jobs to launch for parallel training, default is to
            launch %(default)s jobs.""")

        group.add_argument(
            '-k', '--njobs-feats', type=int, default=20, metavar='<njobs>',
            help="""number of jobs to launch for feature computations, default is to
            launch %(default)s jobs.""")

        return parser
