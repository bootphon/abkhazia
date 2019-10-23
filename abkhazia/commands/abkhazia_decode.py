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
"""Implementation of the 'abkhazia decode' command"""

import argparse
import os
import textwrap

from abkhazia.commands.abstract_command import AbstractKaldiCommand
from abkhazia.corpus import Corpus
import abkhazia.decode as decode
import abkhazia.utils as utils
import abkhazia.kaldi as kaldi


class _DecodeBase(AbstractKaldiCommand):
    # name of subcommand in command-line
    name = NotImplemented

    # one line description of the subcommand
    description = NotImplemented

    # multiline detailed description
    _long_description = NotImplemented

    @classmethod
    def long_description(cls):
        return textwrap.dedent(cls._long_description)

    @classmethod
    def add_parser(cls, subparsers):
        """Return a parser for the align command"""
        # get basic parser init from AbstractCommand
        parser, dir_group = super(_DecodeBase, cls).add_parser(
            subparsers, name=cls.name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.description = cls.long_description()

        dir_group.add_argument(
            '-l', '--language-model', metavar='<lm-dir>', default=None,
            help='''the language model recipe directory. If not specified, use
            <lm-dir>=<corpus>/language.''')

        dir_group.add_argument(
            '-a', '--acoustic-model', metavar='<am-dir>', default=None,
            help='''the acoustic model recipe directory. If not specified, use
            <am-dir>=<corpus>/acoustic.''')

        dir_group.add_argument(
            '-f', '--features', metavar='<feat-dir>', default=None,
            help='''the features directory. If not specified, use
            <feat-dir>=<corpus>/features.''')
        dir_group.add_argument(
            '--fmllr_dir', metavar='<fmllr-dir>',
            default=None,
            help='''the fmllr transform directory. Use if fmllr transform is'''
            '''already computed''')
        # TODO if nnet decoding, add transform-dir in dir_group

        graph_group = parser.add_argument_group('graph making parameters')
        kaldi.options.add_options(graph_group, decode._mkgraph.options())

        decode_group = parser.add_argument_group('decoding parameters')
        kaldi.options.add_options(
            # different for sa, si and nnet
            decode_group, decode.decoders[cls.name].options())

        score_group = parser.add_argument_group('scoring parameters')
        kaldi.options.add_options(score_group, decode._score.options())

        return parser

    @classmethod
    def run(cls, args):
        corpus_dir, output_dir = cls._parse_io_dirs(args)
        log = utils.logger.get_log(
            os.path.join(output_dir, 'decode.log'), verbose=args.verbose)
        corpus = Corpus.load(corpus_dir, validate=args.validate, log=log)

        # get back the features, language and acoustic models directories
        feat = cls._parse_aux_dir(corpus_dir, args.features, 'features')
        lang = cls._parse_aux_dir(corpus_dir, args.language_model, 'language')
        acou = cls._parse_aux_dir(corpus_dir, args.acoustic_model, 'acoustic')
        fmllr = args.fmllr_dir

        # instanciate the kaldi recipe
        recipe = decode.Decode(
            corpus, lang, feat, acou, output_dir, fmllr_dir=fmllr,
            decode_type=cls.name, log=log)
        recipe.njobs = args.njobs
        recipe.delete_recipe = False if args.recipe else True

        # setup the model options parsed from command line
        for k, v in vars(args).items():
            try:
                recipe.set_option(k.replace('_', '-'), v)
            except KeyError:
                pass

        # finally decode the corpus
        recipe.compute()


class _DecodeSi(_DecodeBase):
    name = 'si'
    description = 'decode on mono and tri models'
    _long_description = ''''''


class _DecodeSa(_DecodeBase):
    name = 'sa'
    description = 'decode on tri-sa model'
    _long_description = ''''''


class _DecodeDnn(_DecodeBase):
    name = 'nnet'
    description = 'decode on nnet model'
    _long_description = ''''''


class AbkhaziaDecode(object):
    name = 'decode'
    description = 'decode a corpus (with features) on a trained acoustic model'

    _commands = [_DecodeSi, _DecodeSa, _DecodeDnn]

    @classmethod
    def add_parser(cls, subparsers):
        """Return a parser for the 'abkhazia acoustic' command

        Add a subparser and help message for 'si', 'sa' and 'nnet'
        subcommands.

        """
        parser = subparsers.add_parser(cls.name)
        parser.formatter_class = argparse.RawTextHelpFormatter
        subparsers = parser.add_subparsers(
            metavar='<command>',
            help='possible commands are:\n' + '\n'.join(
                (' {} - {}'.format(
                    c.name + ' '*(11-len(c.name)), c.description)
                 for c in cls._commands)))

        for command in cls._commands:
            command.add_parser(subparsers)

        return parser
