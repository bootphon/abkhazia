# coding: utf-8
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

"""Data preparation for the LibriSpeech corpus

The raw distribution of AESRC

The AESRC dictionary is available for download at

"""

import os, glob, wave
import re

import abkhazia.utils as utils
from abkhazia.corpus.prepare import AbstractPreparatorWithCMU #CMU 

import os
import scipy.io.wavfile
import string


input_dir ='/home/mkhentout/Bureau/Dataset/abkhazia'
#input_dir ='/home/mkhentout/Bureau/Dataset/Datatang-English/data/American English Speech Data'
ponctuation = ['!','?','.']

class AESRCPreparator(AbstractPreparatorWithCMU):
    """Convert the AESRC corpus to the abkhazia format"""
    name = 'AESRC'
    description = 'AESRC Corpus'

    long_description = '''
    AESRC is a corpus of Voice data with format 16kHz , 16bit , Uncompressed wav , Mono
        - Recording environment: relatively quiet indoor, no echo;
        - Recording content: general corpus; some languages include interactive, household, vehicle and digital
        - personnel: 526 People; come from ten different countries; each country has its own proportion of men and women 50% , 50% ;
        - Equipment: Apple mobile phone, Android mobile phone;
        - language: English
        - Application scenarios: speech recognition; voiceprint recognition
   
            • 300 Hours Koreans speak English and collect voice data on mobile phones
            • 500 Hours Russians speak English voice data
            • 200 Hours of Canadians Speaking English, Mobile Phone Collecting Voice Data
            • 800 Hours of American English mobile phone to collect voice data
            • 200 Hours of Portuguese speaking English voice data
            • 500 Hours of Japanese speaking English mobile phone to collect voice data
            • 183 Hours Spaniards Speak English Mobile Phones Collect Voice Data
            • 1,012 Hours of Indian English mobile phone to collect voice data
            • 831 Hours of British English mobile phone collection of voice data
            • 509 Chinese people speak English and collect voice data on mobile phones
                
    '''

    url = ''#?
    audio_format = 'wav'

    silences = []  # SPN and SIL will be added automatically

    variants = []  # could use lexical stress variants...
#ATTENTION sub_dir
    def __init__(self, input_dir,log=utils.logger.null_logger(), copy_wavs=False
                 ):
        super(AESRCPreparator, self).__init__(input_dir, log=log)
        self.copy_wavs = copy_wavs
        
        # list all the wav file in the corpus
        self.wav_files = dict()


        ''' 
            files = glob.glob(os.path.join(input_dir,'*.wav'))
            for f in files:
        '''
        
        print("input_dir = ",input_dir)
        
        for dirs, sub_dirs, f in os.walk(input_dir,'*.wav'):
            print("**************************************\n")
            print("----- =>",f)
            print("sub_dir_before = ",dirs)
            print("input_dir = ",input_dir)

            sub_dir_path = os.path.join(str(input_dir),str(dirs))
            print("sub_dir_after= ",sub_dir_path)
            print("\n len_dirs = ",len(dirs))
            if len(dirs) == 0:
                print("this folder is empty:",dirs)

            else:
                print("hello=",dirs)
                print("/////////////// =>", dirs[-6:-5])
                #if dirs.startswith('G'):
                if dirs[-6:-5] == 'G':
                    print("Hiii=",dirs)
                    for name in f:
                        if name.endswith('.wav'):
                            #print("files = ",f)
                            print("file_name = ",name)
                            #utt_id = os.path.splitext(os.path.basename(f))[0]
                            utt_id = os.path.splitext(os.path.basename(name))[0]
                            print("basename = ",utt_id)
                            print("\n wave_path = ",os.path.join(sub_dir_path,name))
                            self.wav_files[utt_id] = os.path.join(sub_dir_path,name)
        print("looooooooool\n")

        self.phones = dict()
        self.lexicon = dict()
        self.words = set()
        self.text = dict()
        
        

#wavs:subfolder containing the speech recordings in wav, either as files or symbolic links

    def list_audio_files(self):
        print("waves_list = ",self.wav_files.values())
        print("End1\n")
        print("\n****************************\n")
        return self.wav_files.values()

#segments.txt:list of utterances with a description of their location in the wavefiles
    def make_segment(self):
        segments = dict()
        print("22222222")
        for utt_id,wav_file in self.wav_files.items():
            start = 0
            #get the duration of the wave file
            with wave.open(wav_file, 'r') as wav:
                duration = wav.getnframes() / wav.getframerate()
            segments[utt_id] = (utt_id, float(start), float(duration))
        print("End2\n")
        print("\n****************************\n")
        return segments
#G0007S1001 G0007S1001.wav 0 wavefile_duration

#utt2spk.txt: list containing the speaker associated to each utterance
    def make_speaker(self):
        print("33333333")
        utt2spk = dict()
        for utt_id,wav_file in self.wav_files.items():
            speaker_id = utt_id.split("S")[0] #séparer par S(G) 
            utt2spk[utt_id] = speaker_id
        print("End3\n")
        print("\n****************************\n")
        return utt2spk
#G0007S1001-S1001 G00007

#text.txt: transcription of each utterance in word units  
    def make_transcription(self):
        text = dict()

        for utt_id,wav_file in self.wav_files.items():
            text_file = wav_file.replace('.wav','.txt')
            text[utt_id] = open(text_file,'r').read().strip()
            print('utt_id=', utt_id)
            for word in text[utt_id].split(' '):
                self.words.add(word)
            
                #words at the end of the sentence
                '''
                for p in ponctuation:
                    if word.endswith(p):
                        print("ponct before = ",word)
                        print("p = ",p)
                        word = word.replace(p,' ')
                        print("ponctuation after = ",word)
                    else:
                        print("word not ponct= ",word)
                        self.words.add(word)
                '''
        return text
#G0007S1001-S1001 <G0007S1001.txt>

#lexicon.txt: phonetic dictionary using that inventory
    def make_lexicon(self):
        cmu = dict()
        text = dict()
        ponctuation = ['!','?','.',',',';',':','-']
        special_char = "!@#$%^&*()-+?_=,<>/"

        for utt_id,wav_file in self.wav_files.items():
            text_file = wav_file.replace('.wav','.txt')
            text[utt_id] = open(text_file,'r').read().strip()
            print('utt_id=', utt_id)
            for word in text[utt_id].split(' '):
                print("WORD = ",word)
                self.words.add(word)
                

        for line in utils.open_utf8(self.cmu_dict, 'r').readlines():
            # remove newline and trailing spaces
            line = line.strip()
            # skip comments
            if not (len(line) >= 3 and line[:3] == u';;;'):
                # parse line
                word_cmu, phones = line.split(u'  ')
                #print("word_cmu = ",word_cmu)
                #print("phones = ",phones)
                # skip alternative pronunciations, the first one
                # (with no parenthesized number at the end) is
                # supposed to be the most common and is retained
                if not re.match(r'(.*)\([0-9]+\)$', word_cmu):
                    # ignore stress variants of phones
                    cmu[word_cmu] = re.sub(u'[0-9]+', u'', phones).strip()
        
        print("end charging cmu")
        for word in self.words:
            print("Word = ",word.upper())
            last_char=word[-1]

            #ponctuation
            if last_char in ponctuation:
                
                #word.replace(i," ")
                word2 = word.replace(last_char,"")
            else:
                    
                word2 = word
            
            #special char
            for c in word2:
                if c in special_char:
                    print("special_word= ")
                    word3 = word2.replace(c,"")
                else:
                    print("no special_word")
                    word3 = word2
            try: 
                print("cmu[word3.upper()]= ",cmu[word3.upper()])
                self.lexicon[word3] = cmu[word3.upper()]
                print("lexicon_word",self.lexicon[word3])
            except ValueError:
                print("Problem on lexicon!!")
                #put it on file

            for phones in self.lexicon[word3]:
                print("word2 =>",word3)
                print("phone_lexicon",self.lexicon[word3])
                phones = self.lexicon[word3].split(' ')
                
                for phone in phones:
                    print("phone= ",phone)   
                    self.phones[phone] = phone
        return self.lexicon


  

        
