# coding: utf-8
# Copyright 2016 Thomas Schatz, Xuan Nga Cao, Mathieu Bernard
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

"""Data preparation for the Xitsonga corpus"""

# Corrections:
#   text.txt:
#     removed SIL-ENCE at the beginning and end of each sentence
#     replaced [s] by <NOISE>
#   lexicon.txt:
#     removed <UNK> SPN entry (but left <unk> SPN)
#     replaced [s] nse by <noise> NSN as this seems to correspond to noise
#     added words not found in the dictionary (were forgotten from the dev set)
#   phones.txt:
#     removed nse nse
#   silences.txt:
#     added NSN
#
# Pour plus tard:
#   phones.txt: IPA des trucs peut-être à standardiser


import os
import re

from abkhazia.utils import list_files_with_extension
from abkhazia.prepare import AbstractPreparator

class XitsongaPreparator(AbstractPreparator):
    """Convert the Xitsonga corpus to the abkhazia format"""

    name = 'xitsonga'
    description = 'NCHLT Xitsonga Speech Corpus'

    long_description = '''
    Orthographically transcribed broadband speech corpus of
    approximately 56 hours, including a test suite of 8 speakers.'''

    url = 'http://rma.nwu.ac.za/index.php/nchlt-speech-corpus-ts.html'
    audio_format = 'wav'

    # IPA transcriptions for all phones
    phones = {
        'n\'': u'ɳ',
        'K': u'ɬ',
        'tl_>': u'tl\'',
        'tl_h': u'tlʰ',
        'd': u'd',
        'E': u'Ɛ',
        'a': u'a',
        'gh\\': u'gɦ',
        'j': u'j',
        'tj_h': u'tjʰ',
        'u': u'u',
        'd_0Z': u'ʤ',
        'k': u'k',
        'g': u'g',
        'pj_h': u'pjʰ',
        'dz`h\\': u'dʐɦ',
        'dZh\\': u'ʤh',
        'J': u'ɲ',
        'n_h': u'nɦ',
        'tj': u'tj',
        'bj': u'bj',
        'v': u'v',
        'B': u'β',
        's': u's',
        'S': u'ʃ',
        'k_h': u'kʰ',
        'pj_>': u'pj\'',
        'tS_>': ur'ts\ʼ',
        'tS_h': u'tsʰ',
        'b': u'b',
        'z': u'z',
        'dz`': u'dʐ',
        'b_<': u'ɓ',
        'w': u'w',
        'r': u'r',
        't_h': u'tʰ',
        'rh\\': u'rɦ',
        'm_h': u'mɦ',
        's`': u'ʂ',
        'p_h': u'pʰ',
        'f': u'f',
        'i': u'i',
        'dh\\': u'dɦ',
        'h\\': u'ɦ',
        'O': u'ɔ',
        'n': u'n',
        'N': u'ŋ',
        'dK\\': u'dɮ',
        'dK': u'dɬ',
        '!\\': u'!',
        'm': u'm',
        'dj': u'dj',
        'l': u'l',
        'p': u'p',
        't_>': u't\'',
    }

    silences = [u"NSN"]  # SPN and SIL will be added automatically

    variants = []  # could use lexical stress variants...

    def __init__(self, input_dir, output_dir=None,
                 verbose=False, njobs=1, copy_wavs=False):
        # call the AbstractPreparator __init__
        super(XitsongaPreparator, self).__init__(
            input_dir, output_dir, verbose, njobs)

        self.copy_wavs = copy_wavs

    def list_audio_files(self):
        # get the list of wav files in corpus, relative to input_dir
        inputs = [os.path.join('audio', wav) for wav in
                  list_files_with_extension(
                      os.path.join(self.input_dir, 'audio'), '.wav')]

        outputs = [os.path.basename(wav).replace('nchlt_tso_', '')
                   for wav in inputs]

        return inputs, outputs

    def make_segment(self):
        outfile = open(self.segments_file, "w")
        for wav_file in list_files_with_extension(self.wavs_dir, '.wav'):
            bname = os.path.basename(wav_file)
            utt_id = bname.replace('.wav', '')
            outfile.write(utt_id + ' ' + bname + '\n')
        self.log.debug('finished creating segments file')

    def make_speaker(self):
        outfile = open(self.speaker_file, "w")
        for wav_file in list_files_with_extension(self.wavs_dir, '.wav'):
            bname = os.path.basename(wav_file)
            utt_id = bname.replace('.wav', '')
            # extract the first 3 characters from filename to get speaker_ID
            m_speaker = re.match("(.*)_(.*)", bname)
            if m_speaker:
                speaker_id = m_speaker.group(1)
                outfile.write(utt_id + ' ' + speaker_id + '\n')
        self.log.debug('finished creating utt2spk file')

    def make_transcription(self):
        outfile = open(self.transcription_file, "w")

        # get all the utt ID to make sure that the trs match with the
        # wav files
        list_utt = []
        with open(self.segments_file, 'r') as segments:
            for line in segments:
                m_segment = re.match('(.*) (.*)', line)
                if m_segment:
                    list_utt.append(m_segment.group(1))

        list_total = []
        trs_dir = os.path.join(self.input_dir, 'transcriptions')
        for utts in list_files_with_extension(trs_dir, '.xml'):
            with open(utts) as infile:
                # store each file as one string and split by tag
                data = ' '.join([line.replace('\n', '')
                                 for line in infile.readlines()])

                # append the list to the main list
                list_total.extend(data.split('</recording>'))
        self.log.debug("finished extracting the recording tags")

        # Go through each recording and extract the text and utt_id
        # according to pattern
        for i in list_total:
            m_text = re.match(
                "(.*)<recording audio=(.*).wav(.*)<orth>(.*)</orth>", i)
            if m_text:
                utt_id = m_text.group(2)
                text = m_text.group(4)
                # remove beginning of wav path to have utt_id
                utt_id = re.sub("(.*)nchlt_tso_", "", utt_id)
                # replace [s] by <NOISE>
                text = text.replace("[s]", "<NOISE>")
                # check that the text has the equivalent wav and write
                # to outfile
                if utt_id in list_utt:
                    outfile.write(utt_id + ' ' + text + '\n')
                else:
                    raise IOError('bad utterance: {}'.format(utt_id))
        self.log.debug('finished creating text file')


    # To do this, we need to get the mlfs for the language. Not sure
    # it is available on the NCHLT website.
 
    def make_lexicon(self):
        list_total = []
        list_file = []
        list_line = []
        list_word = []
        list_phn = []
        dict_word = {}
        os.path.join(self.input_dir, 'audio')
        out_temp = open(os.path.join(self.output_dir, 'temp.txt'), "w")
        out_lex = open(self.lexicon_file, "w")
        #out_temp = open (outfile_temp, "w")
        for mlfs in list_files_with_extension(
            os.path.join(self.input_dir, 'mlfs_tso'),r'nchlt\.mlf'):
            with open (mlfs) as infile_mlf:
                #join all lines together into one string but still keeping new line character
                data = '\n'.join([line.replace('\n', '') for line in infile_mlf.readlines()])
                #split into a list of files ("." is the separator)
                list_file = re.split('\.\n', data)
                #increment the total list which will be a list containing all small files
                list_total.extend(list_file)
            infile_mlf.close()
        #Go through each small file      
        for i in list_total:
            #split into a list of words (separator is "[0-9]+ [0-9]+ sp (.*)")
            list_word = re.split('[0-9]+ [0-9]+ sp (.*)', i)
            for w in list_word:
                w = w.strip()
                #split into lines
                list_line = w.split('\n')
                for l in list_line:
                    #split each line into tokens
                    list_phn = l.split()
                    #if the line contains the word, extract word + phone
                    if (len(list_phn) == 5):
                        #exclude the silence word
                        if (list_phn[4] == 'SIL-ENCE'):
                            continue
                        #otherwise, extract just phone corresponding to word already extracted
                        else:
                            out_temp.write(list_phn[4] + '\t' + list_phn[2])
                    elif (len(list_phn) == 4):
                        out_temp.write(' ' + list_phn[2])
                out_temp.write('\n')
        out_temp.close()
        self.log.debug ('finished writing temp file')
            
        #open temp dictionary
        in_temp = open(os.path.join(self.output_dir, 'temp.txt'), "r")
        #add these 2 entries in the dict
        out_lex.write ('<noise> NSN\n')
        out_lex.write ('<unk> SPN\n')
        for line in in_temp:
            line = line.strip()
            m_file = re.match("(.*)\t(.*)", line)
            if m_file:
                word = m_file.group(1)
                phn = m_file.group(2)
                #if word not in the lexicon, add entry
                if word not in dict_word:
                    if (word == "[s]"):
                        continue
                    else:
                        dict_word[word] = phn
        #write lexicon to file, sorted by alphabetical order
        for w in sorted(dict_word):
                out_lex.write (w + ' ' + dict_word[w] + '\n')
        in_temp.close()
        self.log.debug('finished creating lexicon file')
        #remove temp file
        os.remove(os.path.join(self.output_dir, 'temp.txt'))