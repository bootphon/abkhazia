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
        group.add_argument('-ov','--overlap',type=float,metavar='<overlap>',
                help=''' a float between 0 and 1.0,represents the overlap
                between the small wave files in output''')
        group.add_argument('-l','--length',type=int,metavar='<length>',
                help=''' an int, usually 1, 10 or 30, represents the length
                of the wave files in output''')
        group.add_argument('-p','--precision',type=float,metavar='<precision>',
                default=0.0125,help=''' specify the precision used to compute 
                the features, by default set for mfcc (see abkhazia's alignment 
                parameters) : 0.0125''')
        group.add_argument('-mp','--mean_phone',type=float,metavar='<mean-phone>',
                default=0.05,help=''' a float, represents the mean length of a 
                phone, is used when creating the small wav files, to avoid having
                a triphone too close to the start or the end of the file. 
                Set to 0.05s by default''')
        group.add_argument('-t','--threshold',type=float,metavar="<alignment>",
                help='''the threshold on the posterior probability. If the
                phone has a posterior probability under the threshold in 
                the alignment, we don't take it into account''')
        group.add_argument('-vd','--vad',type=int,default=0,
                help='''if want to create the vad check this''')
    @classmethod
    def run(cls,args):
        corpus_dir, output_dir = cls._parse_io_dirs(args)
        log = utils.logger.get_log(
                os.path.join(output_dir, 'phonewav.log'),verbose=args.verbose)
        corpus = Corpus.load(corpus_dir, validate=args.validate, log=log)
        
        #load the new speakers text file:
        if args.vad == 0:
            new_speaker_dir=os.path.join(os.path.dirname(os.path.dirname(output_dir)),'new_speakers/new_speakers.txt')
            new_speakers=cls.read_text(new_speaker_dir)
            new_speakers.remove('')
            
            speaker_set=list(set(new_speakers))
        else:
            speaker_set=[wav for wav in corpus.wavs]
        #log.info('create the noise lexicon')
        #corpus.is_noise()

        log.info('create the list of triphones')
        triphones=corpus.phones_timestamps(1,output_dir,alignment=args.alignment,precision=args.precision,proba_threshold=args.threshold,speaker_set=speaker_set,vad=args.vad)
        
        if args.vad == 0 :
            log.info('write the small wave files')
            corpus.create_mini_wavs(
                   output_dir,duration=args.length,alignment=args.alignment,
                    triphones=triphones,overlap=args.overlap,
                    in_path=corpus_dir,out_path=output_dir,mean_phone=args.mean_phone,new_speakers=new_speakers,speaker_set=speaker_set)
    
    @classmethod
    def read_text(cls,path):
        """Read the alignment txt file at align_path and return a  
        dict(speaker,(phone,start,stop))
        """
        try:
            new_speakers_file=utils.open_utf8(path,'r')
        except IOError:
            return False
        new_speakers_read=new_speakers_file.read()
        new_speakers=new_speakers_read.split('\n')
            
        return(new_speakers)

