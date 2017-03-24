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
"""Implementation of the 'abkazia mergewavs' command"""

import os

from abkhazia.commands.abstract_command import AbstractCoreCommand
from abkhazia.corpus import Corpus
import abkhazia.utils as utils


class AbkhaziaMergeWavs(AbstractCoreCommand):
    '''This class implements the 'abkhazia merge_wavs' command'''
    name = 'merge_wavs'
    description = '''For each speaker in the corpus,'''\
                  '''merge all wav files for this speaker'''

    @classmethod
    def add_parser(cls, subparsers):
        # get basic parser init from AbstractCommand
        parser, _ = super(AbkhaziaMergeWavs, cls).add_parser(subparsers)

        group = parser.add_argument_group('merge_wavs arguments')

        return parser

    @classmethod
    def run(cls, args):
        corpus_dir, output_dir = cls._parse_io_dirs(args)
        log = utils.logger.get_log(
            os.path.join(output_dir, 'merge_wavs.log'), verbose=args.verbose)

        corpus = Corpus.load(corpus_dir, validate=args.validate, log=log)

        corpus.merge_wavs(corpus_dir,output_dir)
        
        corpus.save(os.path.join(output_dir,'data'),no_wavs=True)

