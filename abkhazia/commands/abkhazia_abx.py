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
"""Implementation of the 'abkazia abx' command"""

import os

from abkhazia.commands.abstract_command import AbstractCoreCommand
from abkhazia.corpus import Corpus
import abkhazia.utils as utils


class AbkhaziaAbx(AbstractCoreCommand):

    name='abx'
    description = ' create ABX item list'

    @classmethod
    def add_parser(cls, subparsers):
        # get basic parser init from AbstractCommand
        parser, _ = super(AbkhaziaAbx, cls).add_parser(subparsers)

        group = parser.add_argument_group('abx arguments')
    
        group.add_argument('-a','--alignment',type=str,metavar='<alignment>',
                help='''the path to the alignment text  file''')
        group.add_argument('-p','--precision',type=float,metavar='<features>',
                default=0.0125,help='''a float, by default 0.0125, represents
                the precision for the feature extraction''')

    @classmethod
    def run(cls,args):
        corpus_dir, output_dir = cls._parse_io_dirs(args)
        log = utils.logger.get_log(
                os.path.join(output_dir, 'phonewav.log'),verbose=args.verbose)
        corpus = Corpus.load(corpus_dir, validate=args.validate, log=log)
        
        #log.info('create the noise lexicon')
        #corpus.is_noise()

        log.info('create the list of triphones')
        triphones=corpus.phones_timestamps(1,output_dir,alignment=args.alignment,precision=args.precision,proba_threshold=0)
       


