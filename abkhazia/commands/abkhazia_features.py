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
"""Implementation of the 'abkhazia features' command"""

import argparse
import os

import abkhazia.models.features as features
import abkhazia.utils as utils
import abkhazia.kaldi

from abkhazia.commands.abstract_command import AbstractKaldiCommand
from abkhazia.corpus import Corpus

_type_dict = {
    'bool': bool,
    'int': int,
    'float': float,
    'string': str}


class _FeatBase(AbstractKaldiCommand):
    excluded_options = [
        'debug-mel', 'sample-frequency', 'raw-energy', 'vtln-map',
        'output-format', 'utt2spk', 'channel', 'min-duration', 'snip-edges',
        'htk-compat', 'subtract-mean', 'round-to-power-of-two']

    parsed_options = []

    @classmethod
    def add_parser(cls, subparsers):
        # inherit a basic parser with basic options
        parser, _ = super(_FeatBase, cls).add_parser(subparsers)

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

        opt_parser = parser.add_argument_group(
            '{} features options'.format(cls.name))
        cls.add_kaldi_options(opt_parser)

        return parser

    @classmethod
    def _parse_option(cls, name):
        class customAction(argparse.Action):
            def __call__(self, parser, args, value, option_string=None):
                cls.parsed_options.append((name, value))
        return customAction

    @classmethod
    def _default_overload(cls, name, entry):
        overloaded = {'use-energy': 'false'}
        try:
            return overloaded[name]
        except KeyError:
            return entry.default

    @classmethod
    def add_kaldi_options(cls, parser):
        # get the optional parameters from the kaldi binary
        options = abkhazia.kaldi.get_options(cls.kaldi_bin)

        opt_iter = ((n, e) for n, e in sorted(options.iteritems())
                    if n not in cls.excluded_options)

        for name, entry in opt_iter:
            if entry.type == 'bool':
                parser.add_argument(
                    '--{}'.format(name),
                    metavar='<true|false>',
                    choices=['true', 'false'],
                    default=cls._default_overload(name, entry),
                    help=(entry.help[:-1] if entry.help[-1] == '.'
                          else entry.help) + ', default is %(default)s',
                    action=cls._parse_option(name))
            else:
                parser.add_argument(
                    '--{}'.format(name),
                    metavar='<{}>'.format(entry.type),
                    type=_type_dict[entry.type],
                    default=cls._default_overload(name, entry),
                    help=(entry.help[:-1] if entry.help[-1] == '.'
                          else entry.help) + ', default is %(default)s',
                    action=cls._parse_option(name))

    @classmethod
    def run(cls, args):
        # overload the default of use-energy to be false instead of
        # true (if not already specified in options) TODO unify that
        # with the _default_overload method above
        if all('use-energy' not in c[0] for c in cls.parsed_options):
            cls.parsed_options.append(('use-energy', 'false'))

        corpus_dir, output_dir = cls._parse_io_dirs(args)
        log = utils.get_log(
            os.path.join(output_dir, 'features.log'), verbose=args.verbose)
        corpus = Corpus.load(corpus_dir)

        recipe = features.Features(corpus, output_dir, log=log)
        recipe.type = cls.name
        recipe.use_pitch = utils.str2bool(args.use_pitch)  # 'true' to True
        recipe.use_cmvn = utils.str2bool(args.use_cmvn)
        recipe.options = cls.parsed_options
        recipe.njobs = args.njobs
        recipe.delete_recipe = False if args.recipe else True
        recipe.create()
        recipe.run()
        recipe.export()


class _FeatMfcc(_FeatBase):
    name = 'mfcc'
    description = 'Mel-frequency cepstral coefficients'
    kaldi_bin = 'compute-mfcc-feats'


class _FeatFbank(_FeatBase):
    name = 'fbank'
    description = 'Mel-frequency filterbank'
    kaldi_bin = 'compute-fbank-feats'


class _FeatPlp(_FeatBase):
    name = 'plp'
    description = 'Perceptual linear predictive analysis'
    kaldi_bin = 'compute-plp-feats'


class AbkhaziaFeatures(object):
    name = 'features'
    description = 'compute speech features from a corpus'

    _commands = [_FeatMfcc, _FeatFbank, _FeatPlp]

    @classmethod
    def add_parser(cls, subparsers):
        """Return a parser for the features command

        add a subparser with 'mfcc', 'fbank' and 'plp' entries

        """
        parser = subparsers.add_parser(cls.name)
        parser.formatter_class = argparse.RawTextHelpFormatter
        feat_subparsers = parser.add_subparsers(
            metavar='<command>',
            help='possible commands are:\n' + '\n'.join(
                (' {} - {}'.format(c.name + ' '*(8-len(c.name)), c.description)
                 for c in cls._commands)))

        for command in cls._commands:
            command.add_parser(feat_subparsers)

        return parser
