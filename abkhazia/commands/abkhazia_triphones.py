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
"""Implementation of the 'abkazia triphones' command"""

import os

from abkhazia.commands.abstract_command import AbstractCoreCommand
from abkhazia.corpus import Corpus
import abkhazia.utils as utils


class AbkhaziaTriphones(AbstractCoreCommand):

    name='triphones'
    description = ' create list of triphones for each speaker'

    @classmethod
    def add_parser(cls, subparsers):
        # get basic parser init from AbstractCommand
        parser, _ = super(AbkhaziaTriphones, cls).add_parser(subparsers)

        group = parser.add_argument_group('triphones arguments')
    
        group.add_argument('-a','--alignment',type=str,metavar='<alignment>',
                help='''the path to the alignment text  file''')
        group.add_argument('-m','--merge',type=str,metavar='<merge>',default='False',
                help='''merge the wavs by speaker in input - necessary to create
                the triphones -. Only specify if not already done''')

    @classmethod
    def run(cls,args):
        corpus_dir, output_dir = cls._parse_io_dirs(args)
        log = utils.logger.get_log(
                os.path.join(output_dir, 'phonewav.log'),verbose=args.verbose)
        corpus = Corpus.load(corpus_dir, validate=args.validate, log=log)
        corpus.is_noise()
        if args.merge=='True':
            merge=True
        elif args.merge=='False':
            merge=False
        if merge==True:
            corpus.merge_wavs(
                    '/home/julien/workspace/data/exemple/buckeye','test')
        triphones=corpus.phones_timestamps(1,output_dir,alignment=args.alignment)
        print(type(triphones))

        corpus.create_mini_wavs(output_dir,30,alignment=args.alignment,triphones=triphones,overlap=0.5,in_path=corpus_dir,out_path=output_dir)


