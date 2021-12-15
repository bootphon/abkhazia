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

"""Data preparation for the AESRC corpus

The raw distribution of AESRC

The AESRC dictionary is available for download at ?

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

# The punctuation marks.
_PUNCTUATIONS = re.compile('!-;:"\,<>./?@#$%^&*_~«»¡¿—…')#not (',{}()[])
       
       
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
                            self.wav_files[utt_id] = os.path.join(sub_dir_path,name)
        
        
        self.silence = self.make_silence()
        self.phones = dict()
        self.lexicon = dict()
        #self.words = set()

        self._text = self.text_prepare()
        self.text_pre = dict()
       
        #?
        self.clean_text = dict()
        
        
        

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
        
        return self._text
#EX: G0007S1001-S1001 <G0007S1001.txt>

#lexicon.txt: phonetic dictionary using that inventory
   
    def make_lexicon(self):
        separator = phonemizer.separator.Separator(phone=' ', word=None)
        espeak = phonemizer.backend.EspeakBackend('en-us')

        words = []
        for utt in self._text.values():
            for w in utt.split(' '):
                if(not w):
                    print('\n empty word')
                else:
                    words.append(w)

        self.lexicon = {w: espeak.phonemize([w], separator, strip=True)[0] for w in words}

        for w in words:
            phones = self.lexicon[w].split(' ')
            try:
                for phone in phones:

                    if len(phone) != 0:
                        self.phones[phone] = phone
                    else:
                        print(" ")

            except Exception as e:
                    print("\n lexicon_error")
                    f = open(out_put_error+"error_phone.txt","a")
                    f.close()


        self.lexicon['<unk>'] = 'SPN'

        return self.lexicon
    

#silence
    def make_silence(self):
        f = open('silence.txt','a')
        f.write("SIL \n")
        f.write("Noise")
        f.close()
  

    '''
    #phonimaze full sentence
        def make_lexicon(self):
            separator = phonemizer.separator.Separator(phone=' ',word=';eword ')

            # call text_prepare()
            text = self._text
            print("_text= ",text)
            #text_phonemize = phonemize(text,separator=separator,language='en-us')#backend='espeak',     
            text_phonemize = phonemize(text.values(),separator=separator,language='en-us')ou
            words = [w.strip() for w in text_phonemize.split(';eword') if w.strip()]    

            self.lexicon[text.values()]=words 

            while i < len(words):
                for phones in self.lexicon[word[i]]:                  
                    phones = self.lexicon[word[i]].split(' ')
                    try:                                
                        for phone in phones:
                                    
                            if len(phone) != 0:
                                self.phones[phone] = phone
                            else:
                                print(" ")
                                                                    
                    except Exception as e:
                        print("\n lexicon_error")                        
                        f = open(out_put_error+"error.txt","a")
                        f.close()
                            
                        
            self.lexicon['<unk>'] = 'SPN'     
                    
            return self.lexicon
    '''
    def text_prepare(self):
        clean_text = {}
        #_PUNCTUATIONS = re.compile('!-;:"\,<>./?@#$%^&*_~«»¡¿—…')#not (',{}()[])
        my_punct = ['!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '.',
           '/', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', 
           '`', '{', '|', '}', '~', '»', '«', '“', '-' , '--' , '”']
        
        punct_pattern = re.compile("[" + re.escape("".join(my_punct)) + "]")

        for utt_id,wav_file in self.wav_files.items():
            text_file = wav_file.replace('.wav','.txt')
            text_pre = open(text_file,'r').read().strip()

            #remove punctuation
            #clean_text[utt_id] = re.sub(_PUNCTUATIONS, '', text_pre) #.strip() 
           
            clean_text[utt_id] = re.sub(punct_pattern, "", text_pre.strip())
           
        #self.words.add(text_pre)  
        return clean_text