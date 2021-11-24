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
from phonemizer import phonemize
#from phonemizer.separator import default_separator
import phonemizer
from phonemizer.punctuation import Punctuation
from phonemizer.separator import default_separator


#Oberon
input_dir = '/home/mkhentout/Bureau/Dataset/abkhazia/American English Speech Data'
out_put_error = '/home/mkhentout/Bureau/Dataset/abkhazia/tmp_American English Speech'


'''
input_dir ='/home/mkhentout/Bureau/Dataset/Datatang-English/data/American English Speech'
out_put_error = '/home/mkhentout/Bureau/Dataset/tmp_American English Speech/'

'''
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

    silences = ['SPN','SIL']  # SPN and SIL will be added automatically

    variants = []  # could use lexical stress variants...

    def __init__(self, input_dir,log=utils.logger.null_logger(), copy_wavs=False
                 ):
        super(AESRCPreparator, self).__init__(input_dir, log=log)
        self.copy_wavs = copy_wavs
        
        # list all the wav file in the corpus
        self.wav_files = dict()
        
        for dirs, sub_dirs, f in os.walk(input_dir,'*.wav'):

            sub_dir_path = os.path.join(str(input_dir),str(dirs))
          
            if len(dirs) == 0:
                print("this folder is empty:",dirs)

            else:
                #if dirs.startswith('G'):
                if dirs[-6:-5] == 'G':

                    for name in f:
                        if name.endswith('.wav'):
                            
                            utt_id = os.path.splitext(os.path.basename(name))[0]
                            #print("\n wave_path = ",os.path.join(sub_dir_path,name))
                            self.wav_files[utt_id] = os.path.join(sub_dir_path,name)
        #open silence.txt
        f = open('silence.txt','a')
        f.write("SIL \n")
        f.write("Noise")
        f.close()

        self.phones = dict()
        self.lexicon = dict()
        self.words = set()
        self.text = dict()

        self.words_phoneme =set()
        self.lexicon1 =dict()
        
        

#wavs: subfolder containing the speech recordings in wav, either as files or symbolic links

    def list_audio_files(self):
       
        return self.wav_files.values()

#segments.txt: list of utterances with a description of their location in the wavefiles
    def make_segment(self):
        segments = dict()
        for utt_id,wav_file in self.wav_files.items():
            start = 0
            #get the duration of the wave file
            with wave.open(wav_file, 'r') as wav:
                duration = wav.getnframes() / wav.getframerate()
            segments[utt_id] = (utt_id, float(start), float(duration))
       
        return segments
#EX: G0007S1001 G0007S1001.wav 0 wavefile_duration

#utt2spk.txt: list containing the speaker associated to each utterance
    def make_speaker(self):
        utt2spk = dict()
        for utt_id,wav_file in self.wav_files.items():
            speaker_id = utt_id.split("S")[0] #séparer par S(G) 
            utt2spk[utt_id] = speaker_id

        return utt2spk
#EX: G0007S1001-S1001 G00007

#text.txt: transcription of each utterance in word units  
  
    def make_transcription(self):
        text = dict()   
        punctuations = '''!()-[]{};:"\,<>./?@#$%^&*_~''' #not (')

        for utt_id,wav_file in self.wav_files.items():
            text_file = wav_file.replace('.wav','.txt')
            text[utt_id] = open(text_file,'r').read().strip()
            
            no_punct = ""
            for word in text[utt_id]:
                if word not in punctuations:
                    no_punct = no_punct + word               
            text[utt_id]= no_punct 
        self.words.add(no_punct)
       
        return text
#EX: G0007S1001-S1001 <G0007S1001.txt>

#lexicon.txt: phonetic dictionary using that inventory
   
#phonimaze full sentence
    def make_lexicon(self):
        
        text = dict()
        separator = phonemizer.separator.Separator(phone=' ',word=';eword ')
        punctuations = '''!()-[]{};:"\,<>./?@#$%^&*_~--''' #not (')
        no_punct = ""
        char = 0

        #backend = phonemizer.backend.EspeakBackend(language='en-us')
        
        for utt_id,wav_file in self.wav_files.items():
            print("\n IDDDDDDDD :",utt_id)
            text_file = wav_file.replace('.wav','.txt')
            text[utt_id] = open(text_file,'r').read().strip()
            print("\n text[utt_id] on lexicon ",text[utt_id])
            #phonimazer sentence
            sentence = text[utt_id]
            print("\n sentence on lexicon ",text[utt_id])
        
            sentence_phonemize = phonemize(text[utt_id],separator=separator,language='en-us')#backend='espeak',
            
            for word in sentence:
                
                if word not in punctuations or not word.endswith('.'):
                    no_punct = no_punct + word
            sent1= no_punct.split(' ')#text.split()
                     
            words = [w.strip() for w in sentence_phonemize.split(';eword') if w.strip()] 
            
            i = 0
            # delete the space ' ' on the phonemize sentece
            
        
            print("  sent1 : ",sent1)
            while i < len(sent1)+10:     
                if sent1[i] not in punctuations:
                    self.lexicon[sent1[i]]=words[i]                 

                    for phones in self.lexicon[sent1[i]]:                  
                        phones = self.lexicon[sent1[i]].split(' ')
                    try:                                
                            for phone in phones:
                                
                                if len(phone) != 0:
                                    self.phones[phone] = phone
                                else:
                                    print(" ")
                                                               
                    except Exception as e:
                        print("\nLexicon error")                        
                        f = open(out_put_error+"error.txt","a")
                        
                        f.close()
                        
                    i += 1 
                else:
                    print("hhhhh")   
        self.lexicon['<unk>'] = 'SPN'         
                       




          
        '''
        separator = phonemizer.separator.Separator(phone=' ',word=';eword ')
        # text.txt doest not exist yet 
        f = self.text()
        
        lines =f.readlines()
        i = 0
        # Strips the newline character
        for line in Lines:
            i += 1
            print("Line{}: {}".format(i, line.strip()))
            for word in line.split(' ',1): #ignore the 1st word
                word_phonemize = phonemize(word,separator=separator,language='en-us')#backend='espeak',
             
                words = [w.strip() for w in word_phonemize.split(';eword') if w.strip()] 
           
                self.lexicon[word]=words 

                for phones in self.lexicon[sent1[i]]:                  
                    phones = self.lexicon[sent1[i]].split(' ')
                    try:                                
                            for phone in phones:
                            
                                if len(phone) != 0:
                                    self.phones[phone] = phone
                                else:
                                    print(" ")
                                                               
                    except Exception as e:
                        print("\nLexicon error")                        
                        f = open(out_put_error+"error.txt","a")
                        f.close()
                        
                      
        self.lexicon['<unk>'] = 'SPN'     
        '''           
        return self.lexicon

        