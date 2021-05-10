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

import os
import re

import abkhazia.utils as utils
from abkhazia.corpus.prepare import AbstractPreparatorWithCMU #CMU 

import os
import scipy.io.wavfile

data = []
rate = []
input_dir ='/home/mkhentout/Bureau/Dataset/Datatang-English/data/American English Speech Data'

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
        self.wav_files = []
        for dirpath, dirs, files in os.walk(self.input_dir):
            for f in files:
                m_file = re.match("^(.*)\.wav$", f)
                filename =  os.path.splitext(os.path.basename(f))[0] #get the filename

                if m_file: #not in wav_files:#unique filename
                    if filename in wav_files: #check if the filename already exist
                        prefix = 'X'
                        filename.append(prefix + filename + '.wav') #update the filename
                        self.wav_files.append(os.path.join(dirpath, f))
                
                    else:
                        self.wav_files.append(os.path.join(dirpath, f))

       
#wavs:subfolder containing the speech recordings in wav, either as files or symbolic links

    def list_audio_files(self): 
        return self.wav_files

#segments.txt:list of utterances with a description of their location in the wavefiles
    def make_segment(self):
        segments = dict()
        for wav_file in self.wav_files:
            utt_id = os.path.splitext(os.path.basename(wav_file))[0]
            start = 0
            #get the duration of the wave file
            (source_rate, source_sig) = wav.read(wav_file)
            duration_seconds = len(source_sig) / float(source_rate)

            segments[utt_id] = (utt_id, float(start), float(duration_seconds))
        return segments
#G0007S1001 G0007S1001.wav 0 wavefile_duration

#utt2spk.txt: list containing the speaker associated to each utterance
    def make_speaker(self):
        utt2spk = dict()
        for wav_file in self.wav_files:
            utt_id = os.path.splitext(os.path.basename(wav_file))[0]
            speaker_id = bname.split("S")[0]#séparer par S(G) 
            utt2spk[utt_id] = speaker_id
        return utt2spk
#G0007S1001-S1001 G00007

#text.txt: transcription of each utterance in word units  
    def make_transcription(self):
        transcription = dict()
        for wav_file in self.wav_files:
            utt_id = os.path.splitext(os.path.basename(wav_file))[0]
            sentence = utt_id.append[6:10]
            k = utt_id +'-' +sentence
        for line in open(os.path.join(self.input_dir, "text"), 'r'):

            k, v = cd.strip().split('  ', 1)
            transcription[k] = v
        return transcription
#G0007S1001-S1001 <G0007S1001.txt>

#lexicon.txt: phonetic dictionary using that inventory
    def make_lexicon(self):
        lexicon = dict()
        for line in utils.open_utf8(self.cmu_dict, 'r').readlines():
            # remove newline and trailing spaces
            line = line.strip()

            # skip comments
            if not (len(line) >= 3 and line[:3] == u';;;'):
                # parse line
                word, phones = line.split(u'  ')

                # skip alternative pronunciations, the first one
                # (with no parenthesized number at the end) is
                # supposed to be the most common and is retained
                if not re.match(r'(.*)\([0-9]+\)$', word):
                    # ignore stress variants of phones
                    lexicon[word] = re.sub(u'[0-9]+', u'', phones).strip()

        # add special word: <noise> NSN. special word <unk> SPN
        # will be added automatically during corpus validation
            lexicon['<noise>'] = 'NSN'
        return self.lexicon


    def _make_lexicon(self):
        words = set()
        for utt in self.transcription.values():
            for word in utt.split(' '):
                words.add(word)
        return lexicon

    def _load_cmu(self):
        """Return a dict loaded from the CMU dictionay"""
        cmu = {}
        for line in open(self.cmu_dict, "r"):
            match = re.match(r"(.*)\s\s(.*)", line)
            if match:
                entry = match.group(1)
                phn = match.group(2)
                # remove pronunciation variants
                for var in ('0', '1', '2'):
                    phn = phn.replace(var, '')
                # create the combined dictionary
                cmu[entry] = phn
        return cmu

#phones.txt: phone inventory mapped to IPA(IPA=phone in AESRC )
    def make_phones(self):
        phones = set()
        for line in open(os.path.join(self.input_dir, "lexicon.txt"), 'r'):
            m = re.match("(.*)\t(.*)", line)
            if m:
                phn = m.group(2)
                for p in phn.split(' '):
                    phones.add(p)

        return {v: v for v in phones}
