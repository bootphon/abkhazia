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

input_dir ='/home/mkhentout/Bureau/abkhaziaAmerican English Speech Data'
#input_dir ='/home/mkhentout/Bureau/Dataset/abkhazia/Indian English Speech Data'
#input_dir ='/home/mkhentout/Bureau/Dataset/Datatang-English/data/American English Speech Data'
out_put_error = '/home/mkhentout/Bureau/Dataset/tmp_sentence/'
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
                            #print("file_name = ",name)
                            utt_id = os.path.splitext(os.path.basename(name))[0]
                            #print("\n wave_path = ",os.path.join(sub_dir_path,name))
                            self.wav_files[utt_id] = os.path.join(sub_dir_path,name)
       
        self.phones = dict()
        self.lexicon = dict()
        self.words = set()
        self.text = dict()

        self.words_phoneme =set()
        self.lexicon1 =dict()
        

#wavs:subfolder containing the speech recordings in wav, either as files or symbolic links

    def list_audio_files(self):
       
        return self.wav_files.values()

#segments.txt:list of utterances with a description of their location in the wavefiles
    def make_segment(self):
        segments = dict()
        for utt_id,wav_file in self.wav_files.items():
            start = 0
            #get the duration of the wave file
            with wave.open(wav_file, 'r') as wav:
                duration = wav.getnframes() / wav.getframerate()
            segments[utt_id] = (utt_id, float(start), float(duration))
       
        return segments
#G0007S1001 G0007S1001.wav 0 wavefile_duration

#utt2spk.txt: list containing the speaker associated to each utterance
    def make_speaker(self):
        utt2spk = dict()
        for utt_id,wav_file in self.wav_files.items():
            speaker_id = utt_id.split("S")[0] #séparer par S(G) 
            utt2spk[utt_id] = speaker_id

        return utt2spk
#G0007S1001-S1001 G00007

#text.txt: transcription of each utterance in word units  
    def make_transcription(self):
        text = dict()

        for utt_id,wav_file in self.wav_files.items():
            text_file = wav_file.replace('.wav','.txt')
            text[utt_id] = open(text_file,'r').read().strip()
            #print('utt_id=', utt_id)
            for word in text[utt_id].split(' '):
                self.words.add(word)
            
        return text
#G0007S1001-S1001 <G0007S1001.txt>

#lexicon.txt: phonetic dictionary using that inventory
    '''
    def make_lexicon(self):
        cmu = dict()
        text = dict()

        invalid_char = set(string.punctuation)

        for utt_id,wav_file in self.wav_files.items():
            text_file = wav_file.replace('.wav','.txt')
            text[utt_id] = open(text_file,'r').read().strip()
            
            for word in text[utt_id].split(' '):
                self.words.add(word)
                
        #charging cmu dict
        for line in utils.open_utf8(self.cmu_dict, 'r').readlines():
            # remove newline and trailing spaces
            line = line.strip()
            # skip comments
            if not (len(line) >= 3 and line[:3] == u';;;'):
                # parse line
                word_cmu, phones = line.split(u'  ')
              
                # skip alternative pronunciations, the first one
                # (with no parenthesized number at the end) is
                # supposed to be the most common and is retained
                if not re.match(r'(.*)\([0-9]+\)$', word_cmu):
                    # ignore stress variants of phones
                    cmu[word_cmu] = re.sub(u'[0-9]+', u'', phones).strip()      
        print("end charging cmu")


        for word in self.words:  
            last_char=word[-1]
            
            #delete the ponctuation char
            if last_char in invalid_char:  
                word2 = word.replace(last_char,"")
                #print("word2_after_deleting_last=",word2)
            else:       
                word2 = word
                #print("word2_without_last =",word2)

            
            #special char on some accent like(-): eight-eight
            
            c = '-'
            word_list = []
               
            if c in word2: #check if (-) exist
                
                word2 = word2.replace(c," ")
                #print("word_after_special_chr = ",word2)
                  
                part1,part2 = word2.split(' ',1)
                #print("First_part = ",part1)
                #print("second_part = ",part2)
                word_list.append(part1)
                word_list.append(part2)
                #print("list_word_with_c=",word_list)
                
            else:                
                word_list.append(word2)
                #print("list_word_no_c=",word_list)

            for word_c in word_list:
                try: 
                        
                    self.lexicon[word_c] = cmu[word_c.upper()]
                    #print("lexicon_word",self.lexicon[word_c])
                    for phones in self.lexicon[word_c]:
                        phones = self.lexicon[word_c].split(' ')
                            
                        for phone in phones:
                            #print("phone= ",phone)   
                            self.phones[phone] = phone

                except Exception as e: 
                    print("Lexicon Error : ",e)
                    f = open(out_put_error+"error.txt","w")
                    f.write(word_c+"\n")
                    #f.write(phone)+"\n"
                    f.close()
        return self.lexicon

    '''
    '''
    def make_lexicon(self):
        print("make_lexicon")
        text = dict()
        invalid_char = ['-','--','',"`","'"]
        for utt_id,wav_file in self.wav_files.items():
            text_file = wav_file.replace('.wav','.txt')
            text[utt_id] = open(text_file,'r').read().strip()
            #phonimazer sentence
            phonemizer(text[utt_id])
            
            for word in text[utt_id].split(' '):
                self.words.add(word)
                
        for word in self.words:  
            #phonemize_word = phonemize(word)
            separator = phonemizer.separator.Separator(phone=' ', word='')
            punctuation_marks=Punctuation.default_marks()
            if word not in invalid_char :

                try:    
                    print('\n')
                    self.lexicon[word] = phonemize(word,separator=separator,punctuation_marks=punctuation_marks,preserve_punctuation=True)
                    for phones in self.lexicon[word]:
                        phones = self.lexicon[word].split(' ')
                    
                        for phone in phones:
                            
                            if len(phone) != 0:
                                self.phones[phone] = phone
                except Exception as e:
                    print("Lexicon error")
                    f = open(out_put_error+"error.txt","a")
                    f.write(word+"\n")
                    f.close()
            else:
                
                print("\n")
               
                print("\n This word don't exist on lexicon",word)
                f = open(out_put_error+"error2.txt","a")
                f.write(word+"\n")
                f.close()
        return self.lexicon
  

    #phonimaze full sentence
    def make_lexicon(self):

        text = dict()
        invalid_char = ['-','--','',"`","'"]
        ponctuation = set(string.punctuation)

        for utt_id,wav_file in self.wav_files.items():
            text_file = wav_file.replace('.wav','.txt')
            text[utt_id] = open(text_file,'r').read().strip()
            
            #phonimazer sentence
            sentence = text[utt_id]
            print("sentence = ",sentence)

            punctuation_marks=Punctuation.default_marks()
            separator = phonemizer.separator.Separator(phone=' ',word=';eword ')
           
            sentence_phonemize = phonemize(text[utt_id],separator=separator,backend='espeak', language='en-us')#preserve_punctuation=False)
            print("sentence_phonemize= ", sentence_phonemize)

               
            for word in sentence.split(' '):#text[utt_id]
                if len(word) != 0:
                    print("Word = ",word)
                    self.words.add(word)
          
            #text_phonemize
            for word_phonemize in sentence_phonemize.split(' '):
                if len(word_phonemize)!=0:
                    print("Word_phonemize = ",word_phonemize)
                    self.words_phoneme.add(word_phonemize)
            sent2 = sentence_phonemize
            print("\nsent2 = ",sent2)
            
            sent1= sentence.split(' ')#text.split()
            print("\n sent1 = ",sent1)
            #add words
            

            words = [w.strip() for w in sentence_phonemize.split(';eword') if w.strip()] 
            print("wwwwwww = ",words)
        
            i = 0
            
            sent1 = ' '.join(sent1).split()
                
            print(" SSSSS = ",sent1)
               
                
            print('len= ',len(sent1))
            while i < len(sent1):
                print('\n ************* \n')
              
                
                self.lexicon[sent1[i]]=words[i] 
                print("sent1[i] =",sent1[i])
                print("words[i] = ",words[i] )
                #i += 1
            
                
                try:   
                    for phones in self.lexicon[sent1[i]]:
                    
                        phones = phones.split(' ')
                                        
                        #print("\n here in phone = ",phones)
                
                        for phone in phones:
                            #print("\_phone=",phone)   
                            if len(phone) != 0:
                                self.phones[phone] = phone
                            else:
                                print("\nhhhhhhhhhhhhhhhhhhhhhhhhhhh\n")
                          

                        
                    
                
                except Exception as e:
                    print("\nLexicon error")                        
                    f = open(out_put_error+"error.txt","a")
                    f.write(words[i]+"\n")
                    f.close()
                
                i += 1     
                

        print("*** =",self.lexicon)
        return self.lexicon
    '''
#phonimaze full sentence
    def make_lexicon(self):

        text = dict()
        invalid_char = ['-','--','',"`","'"]
        ponctuation = set(string.punctuation)

        for utt_id,wav_file in self.wav_files.items():
            text_file = wav_file.replace('.wav','.txt')
            text[utt_id] = open(text_file,'r').read().strip()
            
            #phonimazer sentence
            sentence = text[utt_id]
            print("Sentence = ",sentence)

            punctuation_marks=Punctuation.default_marks()
            separator = phonemizer.separator.Separator(phone=' ',word=';eword ')
            sentence_phonemize = phonemize(text[utt_id],separator=separator,language='en-us')#backend='espeak',
            print("Sentence_phonemize= ", sentence_phonemize)

            sent1= sentence.split(' ')#text.split()
            print("\nsent1 = ",sent1)
            words = [w.strip() for w in sentence_phonemize.split(';eword') if w.strip()] 
            print("words_eword = ",words)
            i = 0
            # delete the space ' ' on the phonemize sentece
            sent1 = ' '.join(sent1).split()
            size_1 = len(sent1) 
            size_2 = len(sentence_phonemize)
            size_3 = len(words)

            print("Size_1 = ",len(sent1))
            print("Size_3 = ",size_3)

            if size_1 == size_3:#2

                while i < len(sent1):
                    print('\n ************* \n')
                
                    self.lexicon[sent1[i]]=words[i] 
                    print("sent1[i] =",sent1[i])
                    print("words[i] = ",words[i] )
                    #i += 1

                    
                    #print("8888888888 = ",self.lexicon[sent1[i]])
                     
                    for phones in self.lexicon[sent1[i]]:#!! sent1
                        print("phone1 =",phones)
                        phones = self.lexicon[sent1[i]].split(' ')
                    try:                       
                            print("\n here in phone2 = ",phones)
                    
                            for phone in phones:
                                print("\_phone=",phone)   
                                if len(phone) != 0:
                                    self.phones[phone] = phone
                                else:
                                    print("\nhhhhhhhhhhhhhhhhhhhhhhhhhhh = ",phone)
                     
                    except Exception as e:
                        print("\nLexicon error")                        
                        f = open(out_put_error+"error.txt","a")
                        #f.write(words+"\n")
                        f.close()
                    
                    i += 1     
                    
            else:
                print('\n++++++++++++++++++++++++++++\n')
                print("size_1 != size_2")
                print("\n text =",text[utt_id])
                separator = phonemizer.separator.Separator(phone=' ', word='')
                punctuation_marks=Punctuation.default_marks()
                for word in text[utt_id].split(' '):
                    print('1111word = ',word)
                    self.words.add(word)

                for word in self.words:  
                    print("self_words = ",self.words)
                    
                    if word not in invalid_char :
                        print('2222word = ',word)
                        try:    
                            print('\n')
                            self.lexicon[word] = phonemize(word,separator=separator,punctuation_marks=punctuation_marks,preserve_punctuation=True)
                            print("8nhhhh =",self.lexicon)

                            for phones in self.lexicon[word]:
                                print("11 =",phones)
                                phones = self.lexicon[word].split(' ')
                            
                                for phone in phones:
                                    print("22 = ",phone)
                                    if len(phone) != 0:
                                        self.phones[phone] = phone
                           
                        except Exception as e:
                            print("Lexicon error")
                            f = open(out_put_error+"error.txt","a")
                            f.write(word+"\n")
                            f.close()
                    else:
                    
                        print("\n")
                    
                        print("\n This word don't exist on lexicon",word)
                        f = open(out_put_error+"error2.txt","a")
                        f.write(word+"\n")
                        f.close()
                    

        print("*** =",self.lexicon)
        return self.lexicon