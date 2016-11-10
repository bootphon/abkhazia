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

    def phones_timestamps(self,length_context,wav_path,alignment):
        """Get the timestamps of the phones we want to keep
        and add the surrounding context to have length_context seconds
        for each phone
        
        length_context is the total length of the chunks we want to have
        (it should be 1 second, 10 seconds or 30 seconds)
        """
        speakers=self.speakers
        phones_output=defaultdict(list)
        phones=self.read_alignments(alignment)
        i=0
        for spkr in speakers:
            i=i+1
            #For each speaker, group the timestamps by phones    
            sorted_phones=sorted(phones[spkr],key=itemgetter(1))
            triphones=self.list_triphones(sorted_phones)
            if i==1:
                print triphones[0:3]
            ##Add the phones to the list of phones we want to keep
            ##until we reach a file of 10 minutes for this speaker
            #time=0
            #while (time<60):
            #    #pick a random phone and a random timestamp 
            #    u=random.randrange(0,len(sorted_phones))
            #    v=random.randrange(0,len(sorted_phones[u]))
            #    (start,stop)=sorted_phones[u][v]
            #    time = time + (stop-start)
            #    
            #    #add context to the selected phone
            #    time_to_add = (length_context-(stop-start))/2
            #    phones_output[spkr].append((start-time_to_add,stop+time_to_add))
    
    def read_alignments(self,align_path):
        """Read the alignment txt file at align_path and return a  
        dict(speaker,(phone,start,stop))
        """
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
        for utt,start,stop,probability,phone,word in izip(*izip_longest(*alignment)):
            '''in the alignment file, the timestamps are given
            relative to the begining of the utterance '''
            utt_pos=self.corpus.segments[utt][1]
            phones[utt2spk[utt]].append((phone,float(start)+utt_pos,float(stop)+utt_pos))

        return(phones)
    
    def list_triphones(self,phones):
        '''Create a dictionary which lists all available triphones ABC
        output= dict( B , (A,C, start time, stop time))
        '''
        triphones=[]
        silences=set(self.corpus.silences) 
        list_phones=phones
        i=1
        for phone,start,stop in list_phones[1:len(list_phones)-1]:
            start=float(start)
            stop=float(stop)
            previous_phone=list_phones[i-1][0]
            next_phone=list_phones[i+1][0]
        
            if (previous_phone in silences) or (phone in silences) or (next_phone in silences):
                i=i+1
                continue
            previous_phone_stop=float(list_phones[i-1][2])
            next_phone_start=float(list_phones[i+1][1])
             
            #check if the three phones are consecutive
            if (start-(1.0/16000)<previous_phone_stop<start+1.0/16000) and (1.0/16000<next_phone_start<stop+1.0/16000):
                # we can save the current phone 
                
                previous_phone_start=list_phones[i-1][1]
                next_phone_stop=list_phones[i+1][2]
                triphones.append(
                        (previous_phone,phone,next_phone,
                            previous_phone_start,next_phone_stop))
            i=i+1
        return(triphones)


    def create_wav(self,speaker,wav_path,phones_output):
        """Given the times of all the phones we want to keep, we create 
        a wav file containing all the phones and their context"""
        #The names of the wavs at this point should be {speaker}.wav !
        wav_name='.'.join([speaker,'wav'])
        wav_input=os.path.join(wav_path,wav_name)
        wav_output_path=os.path.join(wav_path,'output.wav')
        data=[]

        try:
            wav_file=wave.open(wav_input,'rb')
        except IOError :
            self.log.info("No wav file found in {}".format(wav_input))
            return false
        param=wav_file.getparams()
        length = wav_file.getnframes()

        rate = wav_file.getframerate()
        
        #sort the timestamps by decreasing order (NOT NECESSARY)
        sorted_phones=sorted(phones_output,key=itemgetter(0),reverse=True)
        #get the frames on which the phone is spoken and put them in data 
        output_wav=wave.open(wav_output_path,'wb')
        output_wav.setparams(param)
        output_wav.setnframes(0) # for now the file is empty!
        for (start,stop) in sorted_phones:
            position=rate*start
            length=rate*(stop-start)
            wav_file.setpos(position)
            frames=wav_file.readframes(length)
            output_wav.writeframes(frames)
        output_wav.close()
