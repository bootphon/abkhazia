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


class AbkhaziaFilter(AbstractCoreCommand):
    '''This class implements the 'abkhazia filter' command'''
    name = 'filter'
    description = 'Filter the speech duration distribution of the corpus'

    @classmethod
    def add_parser(cls, subparsers):
        # get basic parser init from AbstractCommand
        parser, _ = super(AbkhaziaFilter, cls).add_parser(subparsers)

        group = parser.add_argument_group('filter arguments')
    
        group.add_argument(
            '-f', '--function', type=str, metavar='<filter>',
            help='''Specifies the filtering function used on the speech distribution.
            Options are : power-law, step, exponential...''')

        group.add_argument(
            '-n','--nb_speaker',default=None,type=int,metavar='<distribution>',
            help='''An integer >1, represents the number of speaker we will keep
                to plot the distribution (if no number specified, we keep all of
                them)''')
           
        group.add_argument(
            '-ns','--new_speakers',type=int,help=''' and integer >1, represents 
            the number of speakers to include in the "family" part''')
        
        group.add_argument(
            '-p','--plot',type=str,metavar='<plot>',default='False',
            help='''If plot==True, a plot of the speech duration distribution and
            of the filtering function will be displayed''')
        
        group.add_argument(
            '-tr','--trim',type=str,default='True',
            help='''if trim==True, the unwanted utterances will be removed from the 
            wav_files, and the segments updated accordingly''')

        return parser

    @classmethod
    def run(cls, args):
        corpus_dir, output_dir = cls._parse_io_dirs(args)
        log = utils.logger.get_log(
            os.path.join(output_dir, 'filter.log'), verbose=args.verbose)

        corpus = Corpus.load(corpus_dir, validate=args.validate, log=log)
        #corpus.is_noise()

        # parse the plot,trim and merge arg as a bool
        if args.plot=="True":
            plot=True
        elif args.plot=="False": 
            plot=False
        else:
            plot=False
        
        if args.trim=="True":
            trim=True
        elif args.trim=="False": 
            trim=False
        else:
            trim=True
        


        # retrieve the test proportion
        (output,not_kept_utterances)=corpus.create_filter(
                output_dir, 
                function=args.function,
                nb_speaker=args.nb_speaker,
                plot=plot,new_speakers=args.new_speakers)
        
        
        if trim==True:
            output.save(os.path.join(output_dir,args.function,'data'),no_wavs=True,copy_wavs=False)
            output.trim(corpus_dir,output_dir,args.function,not_kept_utterances)
        
