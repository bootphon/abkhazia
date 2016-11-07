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
"""Provides the CorpusTrimmer class"""

import os
import shutil
import subprocess
import shlex
import wave
import sys 
import matplotlib.pyplot as plt
import numpy as np

from itertools import * 
from operator import itemgetter, attrgetter, methodcaller
from collections import defaultdict
from abkhazia.utils import open_utf8


class CorpusTrimmer(object):
    """Removes utterances from a corpus"""

    def __init__(self,corpus,not_kept_utts):
        """Removes utterances in 'not_kept_utts' from the
        wavs in the corpus

        'corpus' is an instance of Corpus'

        'not_kept_utts' is a dictionnary of the form : 
        not_kept_utts=(speaker :[(utt1,wav_id,start_time,stop_time),
        (utt1,wav_id,start_time,stop_time)...])
        """

        self.corpus = corpus
        self.not_kept_utts = not_kept_utts
        
        utt_ids, utt_speakers = zip(*self.corpus.utt2spk.iteritems())
        self.speakers = set(utt_speakers)

    def trim(self,corpus_dir,output_dir,function,not_kept_utts):
        """Given a corpus and a list of utterances, this 
        method removes the utterances in the list from the wavs,
        from segments, from the text and from utt2spk
        """
        # return error if sox is not installed 
        try:
            subprocess.check_output(shlex.split('which sox'))
        except:
            raise OSError('sox is not installed on your system')
        print 'hello' 

        # get input and output wav dir
        corpus_dir=os.path.abspath(corpus_dir)
        wav_dir=os.path.join(corpus_dir,'wavs')
        if not os.path.isdir(wav_dir):
            raise IOError('invalid corpus: not found{}'.format(path))
        
        output_dir=os.path.abspath(output_dir)
        output_dir=os.path.join(output_dir,function)
        output_wav_dir=os.path.join(output_dir,'data/wavs')
        if not os.path.isdir(output_wav_dir):
            os.makedirs(output_wav_dir)
        
        # remove utterances from the wavs using sox
        i=0
        for speaker in self.speakers:
            utt_to_remove= self.not_kept_utts[speaker]
            #print utt_to_remove
            wavs_output=[(wav_id,start,stop) for utt_id,(wav_id,start,stop) in utt_to_remove if wav_id in self.corpus.wavs]
            wavs_start_dict=defaultdict(list)
            wavs_stop_dict=defaultdict(list)
            wavs_duration_dict=defaultdict(list)
            for wav_id,start,stop in wavs_output:
                wavs_start_dict[wav_id].append(start)
                wavs_stop_dict[wav_id].append(stop)
                wavs_duration_dict[wav_id].append(stop-start)
            
            for wav in wavs_start_dict:
                wavs_starts_temp=sorted(wavs_start_dict[wav],reverse=True)
                wavs_stop_temp=sorted(wavs_stop_dict[wav],reverse=True)
                wav_name='.'.join([wav,'wav'])
                wav_input_path='/'.join([wav_dir,wav_name])
                wav_output_path='/'.join([output_wav_dir,wav_name])
                
                # Create string of timestamps to remove
                timestamps=''
                for start,stop in zip(wavs_starts_temp,wavs_stop_temp):
                    times='='+str(start)+' '+'='+str(stop)
                    timestamps=' '.join([times,timestamps])
                    
                list_command=['sox',wav_input_path,wav_output_path,'trim 0',timestamps]
                command = ' '.join(list_command)
                    
                 
                subprocess.call(shlex.split(command))              
                print 'for wav {wav_id}, {duration} seconds should have been trimmed'.format(wav_id=wav,duration= sum(wavs_duration_dict[wav]))
                comm='soxi -D '+wav_output_path
                p1=subprocess.check_output(shlex.split(comm))
                print 'checking length of output trimmed file'
                if float(p1)==0:
                    print 'removing empty file'
                    print wav_output_path
                    print p1
                    os.remove(wav_output_path)
                    
                #wav1=wave.open(wav_input_path,'r')
                #wav2=wave.open(wav_output_path,'r')

                #signal1 = wav1.readframes(-1)
                #signal1 = np.fromstring(signal1, 'Int16')

                #signal2 = wav2.readframes(-1)
                #signal2 = np.fromstring(signal2, 'Int16')


                ##If Stereo
                #if wav1.getnchannels() == 2:
                #    print 'Just mono files'
                #    sys.exit(0)

                #f,axarr = plt.subplots(2,sharex=True)
                #axarr[0].plot(signal1)
                #axarr[1].plot(signal2)
                #plt.show()
