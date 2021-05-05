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
from abkhazia.corpus.prepare import AbstractPreparatorWithCMU

import os
import scipy.io.wavfile

data = []
rate = []
r_dir='/home/deepthought/Music/genres/'

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

    url = 
    audio_format = 'wav'

    phones = {
        'IY': u'iː',
        'IH': u'ɪ',
        'EH': u'ɛ',
        'EY': u'eɪ',
        'AE': u'æ',
        'AA': u'ɑː',
        'AW': u'aʊ',
        'AY': u'aɪ',
        'AH': u'ʌ',
        'AO': u'ɔː',
        'OY': u'ɔɪ',
        'OW': u'oʊ',
        'UH': u'ʊ',
        'UW': u'uː',
        'ER': u'ɝ',
        'JH': u'ʤ',
        'CH': u'ʧ',
        'B': u'b',
        'D': u'd',
        'G': u'g',
        'P': u'p',
        'T': u't',
        'K': u'k',
        'S': u's',
        'SH': u'ʃ',
        'Z': u'z',
        'ZH': u'ʒ',
        'F': u'f',
        'TH': u'θ',
        'V': u'v',
        'DH': u'ð',
        'M': u'm',
        'N': u'n',
        'NG': u'ŋ',
        'L': u'l',
        'R': u'r',
        'W': u'w',
        'Y': u'j',
        'HH': u'h',
    }

    silences = [u"NSN"]  # SPN and SIL will be added automatically

    variants = []  # could use lexical stress variants...

    def __init__(self, input_dir,output_dir, log=utils.logger.null_logger(),
                 ):
        super(AESRCPreparator, self).__init__(input_dir, log=log)
         self.copy_wavs = copy_wavs

        # list all the wav file in the corpus
        self.wav_files = []
        for dirpath, dirs, files in os.walk(self.input_dir):
            for f in files:
                m_file = re.match("^(.*)\.wav$", f)
                if m_file:
                    self.wav_files.append(os.path.join(dirpath, f))

       
       
#wavs:subfolder containing the speech recordings in wav, either as files or symbolic links


#each accent
    def list_files_one_accent(self, input_dir,output_dir):
        print ("input_dir"+ input_dir)
        wavs = [] 

        for folder, sub_folders, files in os.walk(input_dir): #r_dir
            print("folder "+folder)
            files = sorted(files)
            for f in files:
                if f.endswith('wav'):
                    print (" wavs file  "+ f)
                    path_f=folder+'/'+f
                
                    shutil.copy(path_f,output_dir)
            return zip(wavs)#!!
#all the accent folder
    def list_audio_files(self,input_path):#input_path = data
        for folder in os.walk(input_path):
            if folder.endswith('English\speech\Data'):
                print("folder is :"+ folder)
                list_files_one_accent(self,folder,folder+'/wavs')
#All accent
    def list_files_all_accent(self,input_path):#input_path = data
        for folder in os.walk(input_path):
            if folder.endswith('English\speech\Data'):
                print("folder is :"+ folder)
                list_files_accent(self,folder,input_path+'/wavs')

#segments.txt:list of utterances with a description of their location in the wavefiles
    def make_segment(self):
        segments = dict()
        for wav_file in self._wavs:#wavs path
            utt_id = os.path.basename(wav_file).replace('.wav', '')#
            segments[utt_id] = (utt_id, None, None)
        return segments

#utt2spk.txt: list containing the speaker associated to each utterance
    def make_speaker(self):
        utt2spk = dict()
        for wav in self._wavs:
            bname = os.path.basename(wav)
            utt_id = bname.replace('.wav', '')
            speaker_id = bname.split("S")[0]#séparer par S(G10208S5450)
            utt2spk[utt_id] = speaker_id
        return utt2spk


#text.txt: transcription of each utterance in word units  
    def make_transcription(self):
        text = dict()
        wav_list = [os.path.basename(w).replace('.wav', '')
                    for w in self._wavs]

        corrupted_wavs = []
        for trs in utils.list_files_with_extension(
                self.input_dir, '.trans.txt'):
            for line in open(trs, 'r'):
                matched = re.match(r'([0-9\-]+)\s([A-Z].*)', line)
                if matched:
                    utt = matched.group(2)

                    lid = len(matched.group(1).split("-")[0])
                    prefix = '00' if lid == 2 else '0' if lid == 3 else ''
                    utt_id = prefix + matched.group(1)

                    if utt_id in wav_list:
                        text[utt_id] = utt
                    else:
                        corrupted_wavs.append(utt_id)
        if corrupted_wavs != []:
            self.log.debug('some utterances have no associated wav: {}'
                           .format(corrupted_wavs))
        return text

#lexicon.txt: phonetic dictionary using that inventory
    def make_lexicon(self):
        # To generate the lexicon, we will use the cmu dict and the
        # dict of OOVs generated by LibriSpeech)
        cmu_combined = dict()

        with open(self.librispeech_dict, 'r') as infile:
            for line in infile:
                if not re.match(";;; ", line):
                    dictionary = re.match("(.*)\t(.*)", line)
                    if dictionary:
                        entry = dictionary.group(1)
                        phn = dictionary.group(2)
                        # remove pronunciation variants
                        phn = phn.replace("0", "")
                        phn = phn.replace("1", "")
                        phn = phn.replace("2", "")
                        # create the combined dictionary
                        cmu_combined[entry] = phn

        with open(self.cmu_dict, 'r') as infile:
            for line in infile:
                if not re.match(";;; ", line):
                    dictionary = re.match(r"(.*)\s\s(.*)", line)
                    if dictionary:
                        entry = dictionary.group(1)
                        phn = dictionary.group(2)
                        # remove pronunciation variants
                        phn = phn.replace("0", "")
                        phn = phn.replace("1", "")
                        phn = phn.replace("2", "")
                        # create the combined dictionary
                        cmu_combined[entry] = phn.strip()

        return cmu_combined

#phones.txt: phone inventory mapped to IPA
    def make_phones(self):
        print("")
#silences.txt: list of silence symbols

def validate_phone_alignment(corpus, alignment, log=utils.logger.get_log()):
    """Return True if the phone alignment is coherent with the corpus

    Return False on any other case, send a log message for all
    suspicious alignments.

    """
    error_utts = set()
    # check all utterances one by one
    for utt in corpus.utts():
        # corpus side
        _, utt_tstart, utt_tstop = corpus.segments[utt]

        # alignment side
        ali_tstart = alignment[utt][0][0]
        ali_tstop = alignment[utt][-1][1]

        # validation
        if utt_tstart != ali_tstart:
            error_utts.add(utt)
            log.warn(
                '%s tstart error in corpus and alignment (%s != %s)',
                utt, utt_tstart, ali_tstart)

        if utt_tstop != ali_tstop:
            error_utts.add(utt)
            log.warn(
                '%s : tstop error in corpus and alignment: %s != %s',
                utt, utt_tstop, ali_tstop)

    if error_utts:
        log.error(
            'timestamps are not valid for %s/%s utterances',
            len(error_utts), len(corpus.utts()))
        return False

    log.info('alignment is valid for all utterances')
    return True
