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

    def create_mini_wavs(self,corpus_dir,duration,alignment,triphones,overlap,in_path,out_path,mean_phone,new_speakers):
        """ create wav files of {duration} seconds, and list,
        for each file, the usable triphones in this file
        """
        self.log.info('creating the mini wavs')
        wavs=self.wavs
        wav_input_path=os.path.join(in_path,'wavs')
        
        # Separate old and new speakers 
        out_path_old = os.path.join(out_path,'old_speakers')
        if not os.path.isdir(out_path_old):
            os.makedirs(out_path_old)
        with open_utf8(os.path.join(out_path_old,'{}s_old.item'.format(duration)),'w') as out:
            ### Write the header ###
            out.write(u'#file onset offset #phone prev-phone next-phone speaker\n')
        
        out_path_new = os.path.join(out_path,'new_speakers')
        if not os.path.isdir(out_path_new):
            os.makedirs(out_path_new)
        with open_utf8(os.path.join(out_path_new,'{}s_new.txt'.format(duration)),'w') as out:
            ### Write the header ###
            out.write(u'#file onset offset #phone prev-phone next-phone speaker\n')
        new_speakers=set(new_speakers)
        #We want the output wave files to be named at random !
        out_timestamps=dict()
        out_triphones=dict()
        nb_output_wav=0
        
        for wav in wavs:
            # based on the fact that one wav = one speaker and that the name 
            # are the same
            #input_name=".".join([wav,'wav'])
            #input_name=os.path.join(wav_input_path,input_name)
            input_name=wavs[wav]
            wav_in=wave.open(input_name,'rb')
            rate=wav_in.getframerate()
            nframes=wav_in.getnframes()
            length_wav=float(nframes)/rate
            tp=triphones[wav]
            starts=np.arange(0,length_wav-duration,overlap*duration)
            stops=starts+duration
            output_timestamps=zip(starts,stops)
            
            out_timestamps[wav],out_triphones[wav] = self.list_triphones_in_wav(
                    tp,output_timestamps,wav,mean_phone)
            nb_output_wav=nb_output_wav+len(out_timestamps[wav])
        x_range=range(nb_output_wav)
        names=random.sample(x_range,nb_output_wav)
        for wav in wavs:
            
            if wav in new_speakers:
                (names,tri_cor)=self.write_wavs(out_timestamps[wav],out_triphones[wav],out_path_new,in_path,wav,names)
                self.write_list_triphone(out_triphones[wav],out_path_new,wav,tri_cor,'new',duration)
            else:
                (names,tri_cor)=self.write_wavs(out_timestamps[wav],out_triphones[wav],out_path_old,in_path,wav,names)
                self.write_list_triphone(out_triphones[wav],out_path_old,wav,tri_cor,'old',duration)

    def list_triphones_in_wav(self,triphones,output_timestamps,wav,mean_phone):
        """for each segment of signal, list the triphones in them, and 
        remove the segments that don't have any triphones
        """
        triphones_start = [(bg,end) for utt,pr,curr,ne,bg,end in triphones]
        triphones = sorted(triphones,key=itemgetter(4))
        triphones_start = sorted(triphones_start,key=itemgetter(0))
         
        output_triphones=defaultdict(list)
        
        # go through each output wave
        wav_index=0
        out_times=[]
        for start,stop in output_timestamps:
            # check if there's a triphone in the wave

            gen=(i for i,x in enumerate(triphones_start) if (start+mean_phone<x[0] and x[1]<stop-mean_phone))
            index=next(gen,None)
            if index is None:
                # if there's no triphone for this file, don't create it
                #out_times.remove((start,stop))
                self.log.debug(
                        'no triphones found for wav from {} to {}, removing the wave'.format(
                            start,stop))
                continue
            
            # while there's triphones in the file, add them to the dict 
            while(index is not None):
                utt,phone1,phone2,phone3,triphone_start,triphone_end=triphones[index]
                # change the timestamps of the triphone to make them relative to the
                # output wav file
                triphone_start=triphone_start-start
                triphone_end=triphone_end-start
                output_triphones[wav_index].append((
                    utt,triphone_start,triphone_end,phone2,phone1,phone3))
                index=next(gen,None)
                self.log.debug(
                'adding triphone {}{}{}, with boundaries{}s-{}s, to wav from {}s to {}s'.format(
                    phone1,phone2,phone3,
                    triphone_start,triphone_end,start,stop))

                            
            
            # when all the triphones have been listed 
            out_times.append((start,stop))
            wav_index=wav_index+1
        self.log.debug("{} wav should be created,{} will actually be created".format(
            wav_index,len(out_times)))
        return(out_times,output_triphones)

    def write_wavs(self,output_timestamps,output_triphones,wav_output_path,wav_input_path,wav,names):
        """ gets the timestamps corresponding to the {duration} seconds files 
        we want to output"""

        wav_input_path=os.path.abspath(wav_input_path)
        wav_input_path=os.path.join(wav_input_path,'wavs')
        wav_output_path=os.path.abspath(wav_output_path)
        if not os.path.isdir(wav_output_path):
            os.makedirs(wav_output_path)
        
        input_name=".".join([wav,'wav'])
        input_name=os.path.join(wav_input_path,input_name)
        try:
            wav_in=wave.open(input_name,'rb')
        except:
            return
            pass
        params=wav_in.getparams()
        triphone_correspondance=[]
        for index,x in enumerate(output_timestamps):
            start=x[0]
            stop=x[1]
            # the name of the output wav is selected at random !
            output_name=".".join([str(names[0]),'wav'])
            triphone_correspondance.append(names[0])
            try:
                names.remove(names[0])
            except IndexError:
                pass
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
        return(names,triphone_correspondance)


    def write_list_triphone(self,output_triphones,
            out_path,wav,triphone_correspondance,distinction,duration):
        """ Writing the list of triphones that occur in each wave file"""

        out_list=[]
        if len(output_triphones)==0:
            return False
        for k in output_triphones:
            for v in output_triphones[k]:
                wav_name=str(triphone_correspondance[k])
                temp=(wav_name,v[1],v[2],v[3],v[4],v[5],wav)
                out_list.append(temp)
        out_path=os.path.join(out_path,'{}s_{}.item'.format(duration,distinction))
        with open_utf8(out_path,'a') as out:
            ### Write the header ###
            #out.write(u'#file onset offset #phone prev-phone next-phone speaker\n')
            for out_wav,v0,v1,v2,v3,v4,v5 in out_list:
                out.write(u'{} {} {} {} {} {} {}\n'.format(out_wav,v0,v1,v2,v3,v4,v5))

        

            
            
