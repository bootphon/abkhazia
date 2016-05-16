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

import os

from abkhazia.commands.abstract_command import AbstractKaldiCommand
from abkhazia.corpus import Corpus
import abkhazia.models.features as features
import abkhazia.utils as utils


class AbkhaziaFeatures(AbstractKaldiCommand):
    name = 'features'
    description = 'compute MFCC features and CMVN statistics'

    @classmethod
    def add_parser(cls, subparsers):
        """Return a parser for the align command"""
        # get basic parser init from AbstractCommand
        parser, _ = super(AbkhaziaFeatures, cls).add_parser(subparsers)

        parser.add_argument(
            '--use-pitch', metavar='<true|false>', choices=['true', 'false'],
            default=utils.config.get('features', 'use-pitch'),
            help="""if true, compute pitch features along with MFCCs,
            default is %(default)s""")

        return parser

    @classmethod
    def run(cls, args):
        corpus, output_dir = cls._parse_io_dirs(args)
        log = utils.get_log(
            os.path.join(output_dir, 'features.log'), verbose=args.verbose)

        recipe = features.Features(Corpus.load(corpus), output_dir, log=log)
        recipe.use_pitch = utils.str2bool(args.use_pitch)  # 'true' to True
        recipe.njobs = args.njobs
        recipe.delete_recipe = False if args.recipe else True
        recipe.create()
        recipe.run()
        recipe.export()
