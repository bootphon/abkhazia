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
"""Implementation of the 'abkhazia features' command"""

import argparse
import os

import abkhazia.models.features as features
import abkhazia.utils as utils

from abkhazia.commands.abstract_command import AbstractKaldiCommand
from abkhazia.corpus import Corpus


class _FeatBase(AbstractKaldiCommand):
    feat_name = NotImplemented
    description = NotImplemented
    kaldi_bin = NotImplemented

    ignored_options = [
        'debug-mel', 'sample-frequency', 'raw-energy', 'vtln-map',
        'output-format', 'utt2spk', 'channel', 'min-duration', 'snip-edges',
        'htk-compat', 'subtract-mean', 'round-to-power-of-two']

    overloaded_options = {'use-energy': 'false'}

    parsed_options = []

    @classmethod
    def add_parser(cls, subparsers):
        # inherit a basic parser with basic options
        parser, dir_parser = super(_FeatBase, cls).add_parser(
            subparsers, name=cls.feat_name)

        dir_parser.add_argument(
            '--h5f', action='store_true',
            help="""if set write features in a h5features file
            named '<output_dir>/feats.h5f'""")

        parser.add_argument(
            '--use-pitch', metavar='<true|false>', choices=['true', 'false'],
            default=utils.config.get('features', 'use-pitch'),
            help="""if true, compute pitch estimation,
            default is %(default)s""")

        parser.add_argument(
            '--use-cmvn', metavar='<true|false>', choices=['true', 'false'],
            default=utils.config.get('features', 'use-cmvn'),
            help="""if true, compute CMVN statistics,
            default is %(default)s""")

        parser.add_argument(
            '--delta-order', metavar='<int>', type=int,
            default=utils.config.getint('features', 'delta-order'),
            help="""compute deltas on raw features, up to the specified order. If
            delta-order is set to 0, deltas are not computed. Default
            is %(default)s.""")

        cls.add_kaldi_options(
            parser.add_argument_group(
                '{} features options'.format(cls.feat_name)))

        return parser

    @classmethod
    def add_kaldi_options(cls, parser):
        """Add the optional parameters from the kaldi feature extractor"""

        def action(name):
            """Append the parsed value to cls.parsed_options"""
            class customAction(argparse.Action):
                def __call__(self, parser, args, value, option_string=None):
                    cls.parsed_options.append((name, value))
            return customAction

        utils.kaldi.add_options_executable(
            parser, cls.kaldi_bin,
            action=action,
            ignore=cls.ignored_options,
            overload=cls.overloaded_options)

    @classmethod
    def run(cls, args):
        # overload the default of use-energy to be false instead of
        # true (if not already specified in options) TODO unify that
        # with the overloaded_options above
        if all('use-energy' not in c[0] for c in cls.parsed_options):
            cls.parsed_options.append(('use-energy', 'false'))

        corpus_dir, output_dir = cls._parse_io_dirs(args, 'features')
        log = utils.logger.get_log(
            os.path.join(output_dir, 'features.log'), verbose=args.verbose)
        corpus = Corpus.load(corpus_dir)

        recipe = features.Features(corpus, output_dir, log=log)
        recipe.type = cls.feat_name
        recipe.use_pitch = utils.str2bool(args.use_pitch)  # 'true' to True
        recipe.use_cmvn = utils.str2bool(args.use_cmvn)
        recipe.delta_order = args.delta_order
        recipe.features_options = cls.parsed_options
        recipe.njobs = args.njobs
        recipe.delete_recipe = False if args.recipe else True
        recipe.compute()

        # export to h5features if asked for
        if args.h5f:
            recipe.log.info('exporting Kaldi ark features to h5features...')
            utils.kaldi.scp_to_h5f(
                os.path.join(recipe.output_dir, 'feats.scp'),
                os.path.join(recipe.output_dir, 'feats.h5f'))


class _FeatMfcc(_FeatBase):
    feat_name = 'mfcc'
    description = 'Mel-frequency cepstral coefficients'
    kaldi_bin = 'compute-mfcc-feats'


class _FeatFbank(_FeatBase):
    feat_name = 'fbank'
    description = 'Mel-frequency filterbank'
    kaldi_bin = 'compute-fbank-feats'


class _FeatPlp(_FeatBase):
    feat_name = 'plp'
    description = 'Perceptual linear predictive analysis'
    kaldi_bin = 'compute-plp-feats'


class AbkhaziaFeatures(object):
    name = 'features'
    description = 'compute speech features from a corpus'

    _commands = [_FeatMfcc, _FeatFbank, _FeatPlp]

    @classmethod
    def add_parser(cls, subparsers):
        """Return a parser for the 'abkhazia features' command

        Add a subparser and help message for 'mfcc', 'fbank' and 'plp'
        subcommands.

        """
        parser = subparsers.add_parser(cls.name)
        parser.formatter_class = argparse.RawTextHelpFormatter
        feat_subparsers = parser.add_subparsers(
            metavar='<command>',
            help='possible commands are:\n' + '\n'.join(
                (' {} - {}'.format(
                    c.feat_name + ' '*(8-len(c.feat_name)), c.description)
                 for c in cls._commands)))

        for command in cls._commands:
            command.add_parser(feat_subparsers)

        return parser
