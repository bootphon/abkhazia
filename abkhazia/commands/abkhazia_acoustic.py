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
import abkhazia.kaldi.acoustic_model as acoustic_model
import abkhazia.utils as utils


class AbkhaziaAcoustic(AbstractRecipeCommand):
    """This class implements the 'abkhazia acoustic' command"""
    name = 'acoustic'
    description = 'train an acoustic model'

    @classmethod
    def run(cls, args):
        # TODO nnet not supported
        if args.type == 'nnet':
            raise NotImplementedError(
                'neural network acoustic modeling not yet implemented')

        corpus, output_dir = cls.prepare_for_run(args)

        # get back the features directory
        feat = (corpus if args.mfcc_features is None
                else os.path.abspath(args.mfcc_features))
        feat += '/features'

        # get back the language model directory
        lang = (corpus if args.language_model is None
                else os.path.abspath(args.language_model))
        lang += '/language'

        # instanciate the kaldi recipe
        recipe = acoustic_model.AcousticModel(
            corpus, output_dir, args.verbose, args.type)

        # setup other recipe parameters from args
        recipe.feat = feat
        recipe.lang = lang
        recipe.num_states_si = args.num_states_si
        recipe.num_gauss_si = args.num_gauss_si
        recipe.num_states_sa = args.num_states_sa
        recipe.num_gauss_sa = args.num_gauss_sa
        recipe.njobs_train = args.njobs_train

        # finally build the acoustic model
        recipe.create()
        recipe.run()

    @staticmethod
    def long_description():
        return """Instantiates and run a kaldi recipe to train a HMM-GMM model on
        an abkhazia corpus and a language model"""

    @classmethod
    def add_parser(cls, subparsers):
        """Return a parser for the align command"""
        # get basic parser init from AbstractCommand
        parser, dir_group = super(AbkhaziaAcoustic, cls).add_parser(subparsers)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.description = cls.long_description()

        parser.add_argument(
            '-j', '--njobs-train', type=int, default=8, metavar='<njobs>',
            help="""number of jobs to launch for parallel training, default is to
            launch %(default)s jobs.""")

        dir_group.add_argument(
            '-l', '--language-model', metavar='<lm-dir>', default=None,
            help='''the language model recipe directory, data is read from
            <lm-dir>/language/lang. If not specified, use <lm-dir>=<corpus>.''')

        dir_group.add_argument(
            '-m', '--mfcc-features', metavar='<feat-dir>', default=None,
            help='''the features directory, data is read from
            <feat-dir>/features/mfcc. If not specified, use
            <feat-dir>=<corpus>.''')

        group = parser.add_argument_group(
            'acoustic model parameters', 'those parameters can also be '
            'specified in the [acoustic] section of the configuration file')

        group.add_argument(
            '-t',  '--type', metavar='<model-type>', default='tri-sa',
            choices=['mono', 'tri', 'tri-sa', 'nnet'],
            help="""the type of acoustic model to train, choose <model-type> in 'mono'
            for monophone, 'tri' for triphone, 'tri-sa' for
            speaker-adapted triphone and 'nnet' for deep neural
            network, default is '%(default)s'.""")

        def config(param):
            return utils.config.get(cls.name, param)

        group.add_argument(
            '--num-states-si', metavar='<int>', type=int,
            default=config('num-states-si'),
            help="""number of states in the speaker-independent triphone model,
            default is '%(default)s'""")

        group.add_argument(
            '--num-gauss-si', metavar='<int>', type=int,
            default=config('num-gauss-si'),
            help="""number of Gaussians in the speaker-independent triphone model,
            default is '%(default)s'""")

        group.add_argument(
            '--num-states-sa', metavar='<int>', type=int,
            default=config('num-states-sa'),
            help="""number of states in the speaker-adaptive triphone model,
            default is '%(default)s'""")

        group.add_argument(
            '--num-gauss-sa', metavar='<int>', type=int,
            default=config('num-gauss-sa'),
            help="""number of Gaussians in the speaker-adaptive triphone model,
            default is '%(default)s'""")

        return parser
