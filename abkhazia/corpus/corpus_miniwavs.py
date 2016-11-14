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
"""Provides the CorpusMiniWavs class"""

import ConfigParser
import random
import matplotlib.pyplot as plt
import numpy as np
import subprocess
import shlex
import os
import shutil
import wave
import contextlib
import math

from collections import defaultdict
from operator import itemgetter
from math import exp
from abkhazia.utils import logger, config, open_utf8


class CorpusMiniWavs(object):
    """A class that creates n seconds files of speech (using a VAD in input)
    and lists the usable triphones in each file.
    """


    def __init__ (self, corpus, log=logger.null_logger()):

        self.log = log
        self.corpus = corpus

        # read inputs from the corpus
        self.segments = self.corpus.segments
        self.wavs = self.corpus.wavs
        self.is_noise = self.corpus.is_noise
        self.silences = set(self.corpus.silences)

    def create_mini_wavs(self,corpus_dir,duration,alignment,triphones,overlap,in_path,out_path):
        """ create wav files of {duration} seconds, and list,
        for each file, the usable triphones in this file
        """
        print 'creating the mini wavs'
        print(type(triphones))
        wavs=self.wavs
        wav_input_path=os.path.join(in_path,'wavs')
        for wav in wavs:
            # based on the fact that one wav = one speaker and that the name 
            # are the same
            input_name=".".join([wav,'wav'])
            input_name=os.path.join(wav_input_path,input_name)
            wav_in=wave.open(input_name,'rb')
            rate=wav_in.getframerate()
            nframes=wav_in.getnframes()
            length_wav=float(nframes)/rate
            tp=triphones[wav]
            starts=np.arange(0,length_wav-duration,overlap*duration)
            stops=starts+duration
            output_timestamps=zip(starts,stops)
            
            output_timestamps,output_triphones = self.list_triphones_in_wav(
                    tp,output_timestamps,wav)
            self.write_wavs(output_timestamps,output_triphones,out_path,in_path,wav)
            self.write_list_triphone(output_triphones,out_path,wav)
    def vad(self,alignment):
        """ creates a vad vector, with values at 1 when there's speech 
        and 0 when there's not (silences, noise etc are put to 0)
        """

        print 'reading the alignment file (again)'

        phones=defaultdict(list)
        speakers=self.speakers
        utt2spk=self.corpus.utt2spk
        vad=defaultdict(list)
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
            corpus=self.corpus
            utt_wav=corpus.segments[utt][0]
            if (phone not in corpus.silences) and (corpus.is_noise[phone]==False):
                vad[wav].append((utt,start,stop,1))
        return(vad)

 
    def list_triphones_in_wav(self,triphones,output_timestamps,wav):
        """for each segment of signal, list the triphones in them, and 
        remove the segments that don't have any triphones
        """
        triphones_start = [bg for pr,curr,ne,bg,end in triphones]
        triphones_start = sorted(triphones_start)
        
        output_triphones=defaultdict(list)
        
        # go through each output wave
        wav_index=0
        print len(output_timestamps)
        out_times=[]
        for start,stop in output_timestamps:
            # check if there's a triphone in the wave

            gen=(i for i,x in enumerate(triphones_start) if start<x<stop)
            index=next(gen,None)
            if index is None:
                # if there's no triphone for this file, don't create it
                #out_times.remove((start,stop))
                continue
            
            # while there's triphones in the file, add them to the dict 
            while(index is not None):
                phone1,phone2,phone3,triphone_start,triphone_end=triphones[index]

                # change the timestamps of the triphone to make them relative to the
                # output wav file
                triphone_start=triphone_start-start
                triphone_end=triphone_end-start
                output_triphones[wav_index].append((
                    triphone_start,triphone_end,phone1,phone2,phone3))
                index=next(gen,None)
                print triphone_start,triphone_end,phone2
            
            # when all the triphones have been listed 
            out_times.append((start,stop))
            wav_index=wav_index+1
        print "{} wav should be created,{} will actually be created".format(wav_index,len(out_times))
        return(out_times,output_triphones)

    def write_wavs(self,output_timestamps,output_triphones,wav_output_path,wav_input_path,wav):
        """ gets the timestamps corresponding to the {duration} seconds files 
        we want to output"""
        print 'reading the wavs in',wav_input_path
        wav_input_path=os.path.abspath(wav_input_path)
        wav_input_path=os.path.join(wav_input_path,'wavs')
        wav_output_path=os.path.abspath(wav_output_path)
        input_name=".".join([wav,'wav'])
        input_name=os.path.join(wav_input_path,input_name)
        try:
            wav_in=wave.open(input_name,'rb')
        except:
            return
            pass
        params=wav_in.getparams()
        for index,x in enumerate(output_timestamps):
            start=x[0]
            stop=x[1]
            if start==22485.0:
                print wav_in.getnframes()
            output_name=".".join([wav,str(index),'wav'])
            output_name=os.path.join(wav_output_path,output_name)
            output_wave=wave.open(output_name,'wb')
            output_wave.setparams(params)
            output_wave.setnframes(0)

            #get the start-stop frames from the input
            rate=wav_in.getframerate()
            wav_in.setpos(start*rate)
            frames=wav_in.readframes(int(rate*(stop-start)))
            
            output_wave.writeframes(frames)
            output_wave.close()


    def write_list_triphone(self,output_triphones,out_path,wav):

        out_list=[]
        for k in output_triphones:
            for v in output_triphones[k]:
                temp=(k,v[0],v[1],v[2],v[3],v[4])
                out_list.append(temp)
        out_list=sorted(out_list,key=itemgetter(1))
        out_path=os.path.join(out_path,'{}.txt'.format(wav))
        with open_utf8(out_path,'w') as out:
            for k,v0,v1,v2,v3,v4 in out_list:
                out.write(u'{} {} {} {} {} {}\n'.format(k,v0,v1,v2,v3,v4))

        

            
            
