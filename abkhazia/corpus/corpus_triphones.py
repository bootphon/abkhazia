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
"""Provides the CorpusTriphones class"""

import os
import shutil
import subprocess
import shlex
import wave
import sys 

import matplotlib.pyplot as plt
import numpy as np
import wave
import contextlib
import random 

from itertools import * 
from operator import itemgetter, attrgetter, methodcaller
from collections import defaultdict
from abkhazia.utils import open_utf8, logger

class CorpusTriphones(object):
    """Create a wav file of phones in a context of n seconds"""

    def __init__(self,corpus,log=logger.null_logger()):
        """For each speaker, pick phones and n seconds of context 
        surrounding these phones, and create a wav file of 10 minutes
        with these phones.
        """

        self.log = log
        self.corpus = corpus
        self.text = corpus.text
        self.phones = defaultdict(list)
        self.wavs = corpus.wavs

        utt_ids, utt_speakers = zip(*self.corpus.utt2spk.iteritems())
        self.speakers = set(utt_speakers)
    
    def phones_timestamps(self,length_context,output_dir,alignment,precision,proba_threshold,speaker_set,vad):
        """Get the timestamps of the phones we want to keep
        and add the surrounding context to have length_context seconds
        for each phone
        
        length_context is the total length of the chunks we want to have
        (it should be 1 second, 10 seconds or 30 seconds)
        """
        speakers=self.speakers
        
        # get the family and new_speakers sets 
        #new_speaker_dir=os.path.join(os.path.dirname(os.path.dirname(output_dir)),'new_speakers/new_speakers.txt')
        #family_dir=os.path.join(os.path.dirname(os.path.dirname(output_dir)),'family/family.txt')
        #family=self.read_family(family_dir)
        #new_speakers=self.read_new_speakers(new_speaker_dir)
        #family.remove('')
        #new_speakers.remove('')
        #
        #speaker_set=family+new_speakers
        #speaker_set=list(set(speaker_set)) # remove duplicate if there are some
        phones_output=defaultdict(list)
        phones=self.read_alignments(alignment,precision,proba_threshold,vad,output_dir)
        i=0
        triphones=defaultdict(list)
        nb_phones=dict()
        self.log.info('computing the triphones')
        for spkr in speaker_set:
            i=i+1
            #For each speaker, group the timestamps by phones
            #this loop is based on the fact that one speaker = one wave file
            sorted_phones=sorted(phones[spkr],key=itemgetter(2))
            nb_phones[spkr]=len(sorted_phones)
            
            self.log.debug('listing triphones for speaker {}'.format(spkr))
            triphones[spkr]=self.list_triphones(sorted_phones,spkr)

        self.log.debug('number of triphones per speakers : {}'.format(nb_phones))
        ##create abx item txt file
        self.triphone2abx_item(triphones,output_dir)

        return(triphones)
    
    def read_alignments(self,align_path,precision,proba_threshold,vad,output_dir):
        """Read the alignment txt file at align_path and return a  
        dict(speaker,(phone,start,stop))
        """
        self.log.info('reading the alignment file')
        phones=defaultdict(list)
        speakers=self.speakers
        utt2spk=self.corpus.utt2spk
        try:
            align=open_utf8(align_path,'r')
        except IOError:
            self.log.info("Error: File not found at {}".format(align_path))
            return False

        #for some lines in alignment.txt, the word corresponding to the phone is
        #put at the end of the line
        alignment=[line.rstrip().split(" ") for line in align if line]
        length_align=len(alignment[0])

        #with open_utf8('alignement.txt','w') as fout,open_utf8('vad.txt','w') as vad:
        if vad:
            if length_align==5:
                with open_utf8(os.path.join(output_dir,'alignement.txt'),'w') as fout,open_utf8(os.path.join(output_dir,'vad.txt'),'w') as vad:
                    for utt,start,stop,proba,phone in alignment:
                        '''in the alignment file, the timestamps are given
                        relative to the begining of the utterance '''
                        try:
                            utt_pos=self.corpus.segments[utt][1]
                            wav=self.corpus.segments[utt][0]
                        except:
                            continue
                        
                        utt_pos=round(utt_pos/precision)*precision
                        phones[utt2spk[utt]].append((utt,phone,float(start)+utt_pos,float(stop)+utt_pos))
                        #self.log.debug('phone {}, wav {} , utt {}'.format(phone,wav,utt))
                        #to output the alignment and the vad
                        fout.write(u'{} {} {} {}\n'.format(wav,float(start)+utt_pos,float(stop)+utt_pos,phone))
                        #if phone not in set(self.corpus.silences):
                        #    vad.write(u'{} {} {}\n'.format(wav,float(start)+utt_pos,float(stop)+utt_pos))
    
            else:
                with open_utf8(os.path.join(output_dir,'alignement.txt'),'w') as fout,open_utf8(os.path.join(output_dir,'vad.txt'),'w') as vad:
                    for utt,start,stop,phone in alignment:
                        '''in the alignment file, the timestamps are given
                        relative to the begining of the utterance '''
                        try:
                            utt_pos=self.corpus.segments[utt][1]
                            wav=self.corpus.segments[utt][0]
                        except:
                            continue
                        utt_pos=round(utt_pos/precision)*precision
                        phones[utt2spk[utt]].append((utt,phone,float(start)+utt_pos,float(stop)+utt_pos))
                        #self.log.debug('phone {}, wav {} , utt {}'.format(phone,wav,utt))
                        #to output the alignment and the vad
                        fout.write(u'{} {} {} {}\n'.format(wav,float(start)+utt_pos,float(stop)+utt_pos,phone))
                        #if phone not in set(self.corpus.silences):
                        #    vad.write(u'{} {} {}\n'.format(wav,float(start)+utt_pos,float(stop)+utt_pos))
 
        else:
            if length_align==5:
                for utt,start,stop,proba,phone in alignment:
                  '''in the alignment file, the timestamps are given
                  relative to the begining of the utterance '''
                  try:
                      utt_pos=self.corpus.segments[utt][1]
                      wav=self.corpus.segments[utt][0]
                  except:
                      continue
                  if float(proba)>proba_threshold:
                    utt_pos=round(utt_pos/precision)*precision
                    phones[utt2spk[utt]].append((utt,phone,float(start)+utt_pos,float(stop)+utt_pos))
                    #self.log.debug('phone {}, wav {} , utt {}'.format(phone,wav,utt))
                  #to output the alignment and the vad
                  #fout.write(u'{} {} {} {}\n'.format(wav,float(start)+utt_pos,float(stop)+utt_pos,phone))
                  #if phone not in set(self.corpus.silences):
                  #    vad.write(u'{} {} {}\n'.format(wav,float(start)+utt_pos,float(stop)+utt_pos))
            elif length_align==4:
                for utt,start,stop,phone in alignment:
                  '''in the alignment file, the timestamps are given
                  relative to the begining of the utterance '''
                  try:
                      utt_pos=self.corpus.segments[utt][1]
                      wav=self.corpus.segments[utt][0]
                  except:
                      continue
                  utt_pos=round(utt_pos/precision)*precision
                  phones[utt2spk[utt]].append((utt,phone,float(start)+utt_pos,float(stop)+utt_pos))
                  #self.log.debug('phone {}, wav {} , utt {}'.format(phone,wav,utt))

        return(phones)
    
    def list_triphones(self,phones,spkr):
        '''Create a dictionary which lists all available triphones ABC
        output= list( (A,B,C, start time, stop time))
        '''
        triphones=[]
        silences=set(self.corpus.silences) 
        list_phones=phones
        if spkr=='M10':
            for ind,x in enumerate(list_phones[:len(list_phones)-1]):
                if ind==0:
                    continue

                utt=x[0]
                phone=x[1]
                start=float(x[2])
                stop=float(x[3])
                previous_phone=list_phones[ind-1][1]
                next_phone=list_phones[ind+1][1]

        for ind,x in enumerate(list_phones[:len(list_phones)-1]):
            if ind==0:
                continue

            utt=x[0]
            phone=x[1]
            start=float(x[2])
            stop=float(x[3])
            previous_phone=list_phones[ind-1][1]
            next_phone=list_phones[ind+1][1]
            if (previous_phone in silences) or (phone in silences) or (next_phone in silences):
                continue 
            previous_phone_stop=float(list_phones[ind-1][3])
            next_phone_start=float(list_phones[ind+1][2])
            #check if the three phones are consecutive
            if ((start-(1.0/16000)<previous_phone_stop<start+1.0/16000)
                    and (1.0/16000<next_phone_start<stop+1.0/16000)):
                # we can save the current phone 
                
                previous_phone_start=list_phones[ind-1][2]
                next_phone_stop=list_phones[ind+1][3]
                triphones.append(
                        (utt,previous_phone,phone,next_phone,
                            previous_phone_start,next_phone_stop))

        return(triphones)

    def triphone2abx_item(self,triphones,out_path):
        """Create the Item list for the ABX task"""
        self.log.info('creating the abx item list')
        out_list=[]
        for k in triphones:
            for v in triphones[k]:
                temp=(v[0],v[4],v[5],v[1],v[2],v[3],k)
                out_list.append(temp)
        out_path=os.path.join(out_path,'phones.item')

        # write the item file
        with open_utf8(out_path,'w') as out:
            ###write the header
            out.write(u'#file onset offset #phone prev-phone next-phone speaker\n')
            for v0,v1,v2,v3,v4,v5,v6 in out_list:
                out.write(u'{} {} {} {} {} {} {}\n'.format(v0,v1,v2,v3,v4,v5,v6))

    def read_family(self,path):
        """Read the alignment txt file at align_path and return a  
        dict(speaker,(phone,start,stop))
        """
        self.log.info('reading the family file')
        speakers=self.speakers
        try:
            family_file=open_utf8(path,'r')
        except IOError:
            self.log.info("Error: File not found at {}".format(path))
            return False
        family_read=family_file.read()
        family=family_read.split('\n')
        return(family)

    def read_new_speakers(self,path):
        """Read the alignment txt file at align_path and return a  
        dict(speaker,(phone,start,stop))
        """
        self.log.info('reading the new_speakers file')
        try:
            new_speakers_file=open_utf8(path,'r')
        except IOError:
            self.log.info("Error: File not found at {}".format(path))
            return False
        new_speakers_read=new_speakers_file.read()
        new_speakers=new_speakers_read.split('\n')
            
        return(new_speakers)

