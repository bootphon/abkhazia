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
"""Provides the CorpusMergeWavs class"""

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

from operator import itemgetter
from math import exp
from abkhazia.utils import logger, config


class CorpusMergeWavs(object):
    """A class for merging the wavs files together for each speaker,
    , at the end of this class, one .wav file = one speaker. This 
    class also edits the segment to have a correction alignment, and
    wavs.
    
    
    corpus : The abkhazia corpus to filter. The corpus is assumed
      to be valid.

    log : A logging.Logger instance to send log messages

    function : A string that specifies the cutting function that
      will be used on the corpus

    plot : A boolean which, if set to true, enables the plotting
      of the speech distribution and the cutting function
    """
    def __init__(self, corpus, log=logger.null_logger(),
                 random_seed=None, prune=True):
        self.log = log
        self.prune = prune
        self.corpus = corpus

        # read utt2spk from the input corpus
        utt_ids, utt_speakers = zip(*self.corpus.utt2spk.iteritems())
        self.utts = zip(utt_ids, utt_speakers)
        self.size = len(utt_ids)
        self.speakers = set(utt_speakers)
        self.limits = dict()
        self.spk2utts = dict()
        self.segments = self.corpus.segments
        self.wavs = self.corpus.wavs
        self.utt2spk=self.corpus.utt2spk
        self.utt2dur=self.corpus.utt2duration()
        self.log.debug('loaded %i utterances from %i speakers',
                       self.size, len(self.speakers))

    def merge_wavs(self,corpus_dir,function):
        """For each speaker, merge all the wav file together, 
        and edit the segments to keep a correct alignment."""
         # return error if sox is not installed 
        try:
            subprocess.check_output(shlex.split('which sox'))
        except:
            raise OSError('sox is not installed on your system')

         # get input and output wav dir
        corpus_dir=os.path.abspath(corpus_dir)
        corpus_dir=os.path.join(corpus_dir,function)
        corpus_dir=os.path.join(corpus_dir,'data')
        wav_dir=os.path.join(corpus_dir,'wavs')
       # if not os.path.isdir(wav_dir):
       #     raise IOError('invalid corpus: not found{}'.format(path))
        

        utt2dur = self.utt2dur
        spk2dur=dict()
        speakers=self.speakers
        spk2utts=self.spk2utts
        utts=self.utts

        for spkr in speakers:
            spk_utts=[utt_id for utt_id, utt_speaker in utts if utt_speaker == spkr]
            duration=sum([utt2dur[utt_id] for utt_id in spk_utts])
            spk2dur[spkr]=duration
            spk2utts[spkr]=spk_utts
            self.log.debug('for speaker %s , total duration is %i',
                            spkr,duration/60)
        self.spk2utts=spk2utts
        
        
        spk2wavs=dict()
        spk2wav_dur=dict()
        for spkr in speakers:
            wav_utt=[self.corpus.segments[utt][0] for utt in spk2utts[spkr]]
            # we want uniq values in the list of wav :
            wav_utt=list(set(wav_utt))
            print wav_utt
            spk2wavs[spkr]=wav_utt
            #first wav file in the list doesn't have an offset since it's first
            spk2wav_dur[spkr]=[]
            spk2wav_dur[spkr].append(0)
            for wav in wav_utt:
                wav_name='.'.join([wav,'wav'])
                wav_path='/'.join([wav_dir,wav_name])
                with contextlib.closing(wave.open(wav_path,'r')) as wav_file:
                    frames = wav_file.getnframes()
                    rate = wav_file.getframerate()
                    duration = frames / float(rate)
                    print('wav file %s has a duration of %d',wav_name,duration)

                #comm="soxi -D "+wav_path
                #print comm
                #p1=subprocess.check_output(shlex.split(comm))
                #spk2wav_dur[spkr].append(float(p1))
                spk2wav_dur[spkr].append(duration)
            if len(spk2wav_dur[spkr])!=len(wav_utt)+1:
                """ length should be the same, as spk2wav_dur declares 
                the length of waves in wav_utt
                """
                raise OSError('error with length detection using soxi')
                #print 'normal'
            #x_range=range(len(spk2wav_dur[spkr]))
            #print x_range
            #plt.clf()
            #plt.bar(x_range,spk2wav_dur[spkr],alpha=0.5)

            cumulated_duration=np.cumsum(spk2wav_dur[spkr])
            print ('cumulated_duration[0] = ',cumulated_duration[0])
            #plt.bar(x_range,cumulated_duration[:len(spk2wav_dur[spkr])],0.50,color='r')
            #plt.show()
            #spk2wav_dur[spkr]=np.cumsum(spk2wav_dur[spkr])
            spk2wav_dur[spkr]=cumulated_duration
            


        #update segments
        for spkr in speakers:
            for utt in spk2utts[spkr]:
                utt_wav_id=self.corpus.segments[utt][0]
                spk2wav_dur_temp=spk2wav_dur[spkr][0:len(spk2wavs[spkr])]
                #print spk2wav_dur_temp
                wav_dur_dict=dict(zip(spk2wavs[spkr],spk2wav_dur_temp))
                offset=wav_dur_dict[utt_wav_id]
                print 'putting offset ',offset,'for wav ',utt_wav_id
                start=self.corpus.segments[utt][1]
                stop=self.corpus.segments[utt][2]

                #the name of the finale wave file will be spkr.wav (ex s01.wav)
                finale_wav_id=spkr
                self.corpus.segments[utt]=finale_wav_id,start+offset,stop+offset

        #merge the wavs 
        spk2list_wav_to_merge=dict() 
        for spkr in speakers:
            wav_name='.'.join([spkr,'wav'])
            wav_input_path='/'.join([wav_dir,wav_name])
            list_wav_to_merge=[]
            for wav in spk2wavs[spkr]:
                wav_to_merge='.'.join([wav,'wav'])
                wav_to_merge='/'.join([wav_dir,wav_to_merge])
                list_wav_to_merge.append(wav_to_merge)

            spk2list_wav_to_merge[spkr]=list_wav_to_merge
            data=[]
            for wav_file in spk2list_wav_to_merge[spkr]:
                wav_to_merge=wave.open(wav_file,'rb')
                print 'for speaker ',spkr,' adding the wave ',wav_file
                data.append( [wav_to_merge.getparams(), wav_to_merge.readframes(wav_to_merge.getnframes())])
                wav_to_merge.close
            output= wave.open(wav_input_path,'wb')
            output.setparams(data[0][0])
            for nb in range(len(spk2wavs[spkr])):
                output.writeframes(data[nb][1])

            output.close()
            #list_command = ["sox"]+list_wav_to_merge+[wav_input_path]
            #print list_command
            #command = " ".join(list_command)
            #subprocess.call(shlex.split(command))
            
        #verify that the merger worked and update wave set
        for spkr in speakers:
            wav_name='.'.join([spkr,'wav'])
            wav_input_path='/'.join([wav_dir,wav_name])

            self.log.debug(os.path.isfile(wav_input_path))

            self.corpus.wavs[spkr]=wav_input_path
            if os.path.isfile(wav_input_path):
                print 'last time'
                #comm="soxi -D "+wav_input_path
                #p1=subprocess.check_output(shlex.split(comm))
                duration=0
                with contextlib.closing(wave.open(wav_input_path,'r')) as f:
                    frames=f.getnframes()
                    rate = f.getframerate()
                    duration=frames/float(rate)
                
                if duration!=spk2wav_dur[spkr][-1]:
                    #raise IOError('the merged wave length is different from the sum of the initial wave file')
                    print duration ,spk2wav_dur[spkr][-1]
                    
            for wav_path in spk2list_wav_to_merge[spkr]:
                if os.path.isfile(wav_path):
                    print wav_path
                    os.remove(wav_path)
                else:
                    print 'no hello'
        #update wav set
        self.corpus.validate()
                



 
