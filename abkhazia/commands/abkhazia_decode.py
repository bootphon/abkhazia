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

import os

from abkhazia.commands.abstract_command import AbstractKaldiCommand
from abkhazia.corpus import Corpus
import abkhazia.models.decode as decode
import abkhazia.utils as utils


class AbkhaziaDecode(AbstractKaldiCommand):
    name = 'decode'

    description = """decode a corpus and provides WER"""

    @classmethod
    def add_parser(cls, subparsers):
        """Return a parser for the align command"""
        # get basic parser init from AbstractCommand
        parser, dir_group = super(AbkhaziaDecode, cls).add_parser(subparsers)

        dir_group.add_argument(
            '-l', '--language-model', metavar='<lm-dir>', default=None,
            help='''the language model recipe directory, data is read from
            <lm-dir>/language. If not specified, use <lm-dir>=<corpus>.''')

        dir_group.add_argument(
            '-a', '--acoustic-model', metavar='<am-dir>', default=None,
            help='''the acoustic model recipe directory, data is read from
            <am-dir>/acoustic. If not specified, use <am-dir>=<corpus>.''')

        dir_group.add_argument(
            '-f', '--features', metavar='<feat-dir>', default=None,
            help='''the features directory, data is read from
            <feat-dir>/features. If not specified, use <feat-dir>=<corpus>.''')

        group = parser.add_argument_group(
            'decoding parameters', 'those parameters can also be '
            'specified in the [decode] section of the configuration file')

        def config(param):
            return utils.config.get(cls.name, param)

        group.add_argument(
            '-s', '--acoustic-scale',
            type=float, metavar='<float>', default=0.1,
            help='''acoustic scale for extracting posterior
            from the final lattice, default is %(default)s''')

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

        # instanciate and run the kaldi recipe
        recipe = decode.Decode(corpus, output_dir, log=log)
        recipe.feat_dir = feat
        recipe.lm_dir = lang
        recipe.am_dir = acou
        recipe.acoustic_scale = args.acoustic_scale
        recipe.njobs = args.njobs
        recipe.delete_recipe = False if args.recipe else True
        recipe.compute()
