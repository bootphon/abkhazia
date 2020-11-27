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
"""Implementation of the 'abkhazia align' command"""

import argparse
import os
from argparse import _SubParsersAction, ArgumentParser

import abkhazia.align as align
import abkhazia.utils as utils
from abkhazia.align.align import AlignNoLattice
from abkhazia.commands.abstract_command import AbstractKaldiCommand
from abkhazia.corpus import Corpus
from abkhazia.features import Features
from abkhazia.language import LanguageModel


class AbkhaziaFastAlign(AbstractKaldiCommand):
    '''This class implements the 'abkhazia align' command'''
    name = 'fast-align'
    description = 'all-in-one forced-alignment command'

    @staticmethod
    def long_description():
        return ('End-to-end forced alignment of a kaldi-compatible corpus.'
                'Can optionally be speaker-adapted, and on monophones or '
                'triphones.')

    @classmethod
    def add_parser(cls, subparsers: _SubParsersAction) -> ArgumentParser:
        """Return a parser for the align command"""
        # get basic parser init from AbstractCommand
        parser, dir_group = super(AbkhaziaFastAlign, cls).add_parser(subparsers)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.description = cls.long_description()

        out_group = parser.add_argument_group('alignment parameters')
        out_group.add_argument(
            '--acoustic-scale', default=0.1, type=float, metavar='<float>',
            help='scaling factor for acoustic likelihoods, '
                 'default is %(default)s')

        out_group = parser.add_mutually_exclusive_group()
        out_group.add_argument(
            '--use-triphone', action="store_true",
            help='Use triphone acoustic model')
        out_group.add_argument(
            '--use-speaker-adapted', action="store_true",
            help='Use speaker-adapted acoustic model')

        out_group = out_group.add_mutually_exclusive_group()
        out_group.add_argument(
            '--post', action='store_true',
            help='write posterior probability of aligned phones')
        out_group.add_argument(
            '--no-lattice', action='store_true',
            help='do not compute lattice, faster but disallow posteriors')

        out_group = parser.add_argument_group('alignment format', description=(
            'by default the output alignement file is phone aligned and '
            'include both words and phones'))
        out_group = out_group.add_mutually_exclusive_group()
        out_group.add_argument(
            '--phones-only', action='store_true',
            help='do not write words in the final alignment file, only phones')
        out_group.add_argument(
            '--words-only', action='store_true',
            help='do not write phones in the final alignment file, only words')

        dir_group.add_argument(
            '-l', '--language-model', metavar='<lm-dir>', default=None,
            help='''the language model recipe directory, data is read from
                <lm-dir>/language. If not specified, will try looking for
                use <lm-dir>=<corpus>. 
                If no language model is present, will compute it from scratch.''')

        dir_group.add_argument(
            '-f', '--features', metavar='<feat-dir>', default=None,
            help='''the features directory, data is read from
            <feat-dir>/features/mfcc. If not specified, use
            <feat-dir>=<corpus>.
            If no features are present, will compute them from scratch.''')

        dir_group.add_argument(
            '-a', '--acoustic-model', metavar='<am-dir>', default=None,
            help='''the acoustic model recipe directory, data is read from
            <am-dir>/acoustic. If not specified, use <am-dir>=<corpus>.
            If no accoustic model is present, will compute it from scratch.
            ''')

        return parser

    @classmethod
    def compute_accoustic(cls, args, corpus_dir):
        # get back the acoustic model directory
        acoustic = (os.path.join(os.path.dirname(corpus_dir), 'acoustic')
                    if args.acoustic_model is None
                    else os.path.abspath(args.acoustic_model))

        # TODO: test for existence, launch recipe if nothing exists
        # compute intermediary acoustic model if needed

    @classmethod
    def run(cls, args):
        # get back the input corpus and output directory
        corpus_dir, output_dir = cls._parse_io_dirs(args)
        log = utils.logger.get_log(
            os.path.join(output_dir, 'align.log'), verbose=args.verbose)
        corpus = Corpus.load(corpus_dir, validate=args.validate, log=log)

        # get back the language model directory
        lang = (os.path.join(os.path.dirname(corpus_dir), 'language')
                if args.language_model is None
                else os.path.abspath(args.language_model))

        if not os.path.isdir(lang):
            recipe = LanguageModel(corpus, lang,
                                   order=3,
                                   level="word")

            recipe.delete_recipe = False if args.recipe else True
            recipe.compute()

        # get back the features directory
        feat = (os.path.join(os.path.dirname(corpus_dir), 'features')
                if args.features is None
                else os.path.abspath(args.features))

        if not os.path.isdir(feat):
            recipe = Features(corpus,
                              feat,
                              type="mfcc",
                              use_cmvn=True)
            recipe.use_cmvn = True
            recipe.njobs = args.njobs
            recipe.delete_recipe = False if args.recipe else True
            recipe.compute()

        # parse the alignment level
        if args.words_only:
            level = 'words'
        elif args.phones_only:
            level = 'phones'
        else:
            level = 'both'

        if level == 'words' and args.post:
            raise NotImplementedError(
                'incompatible options --post and --words-only, '
                'not implemented')

        # instanciate the kaldi recipe creator
        recipe = (AlignNoLattice if args.no_lattice
                  else align.Align)(corpus, output_dir, log=log)
        recipe.njobs = args.njobs
        recipe.level = level
        recipe.with_posteriors = args.post
        recipe.acoustic_scale = args.acoustic_scale
        recipe.lm_dir = lang
        recipe.feat_dir = feat
        recipe.am_dir = acoustic
        recipe.delete_recipe = False if args.recipe else True

        # finally compute the alignments
        recipe.create()
        recipe.run()
        recipe.export()
