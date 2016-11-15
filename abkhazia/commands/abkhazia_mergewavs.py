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
"""Implementation of the 'abkazia filter' command"""

import os

from abkhazia.commands.abstract_command import AbstractCoreCommand
from abkhazia.corpus import Corpus
import abkhazia.utils as utils


class AbkhaziaMergeWavs(AbstractCoreCommand):
    '''This class implements the 'abkhazia mergeWavs' command'''
    name = 'mergeWavs'
    description = 'Filter the speech duration distribution of the corpus'

    @classmethod
    def add_parser(cls, subparsers):
        # get basic parser init from AbstractCommand
        parser, _ = super(AbkhaziaMergeWavs, cls).add_parser(subparsers)

        group = parser.add_argument_group('filter arguments')
    
        group.add_argument(
            '-m','--merge',type=str,default='True',
            help='''if merge==True, all wav files that corresponds to one speaker 
            will be merged, so that in the output folder there are only one wave
            file per speaker''')

        return parser

    @classmethod
    def run(cls, args):
        corpus_dir, output_dir = cls._parse_io_dirs(args)
        log = utils.logger.get_log(
            os.path.join(output_dir, 'filter.log'), verbose=args.verbose)

        corpus = Corpus.load(corpus_dir, validate=args.validate, log=log)

        corpus.merge_wavs(corpus_dir,output_dir)
        
        corpus.save(os.path.join(output_dir,'data'),no_wavs=True)

