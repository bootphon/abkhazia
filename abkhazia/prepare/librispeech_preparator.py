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

"""Data preparation for the LibriSpeech corpus

The raw distribution of LibriSpeech is available at
http://www.openslr.org/12/

The LibriSpeech dictionary is available for download at
http://www.openslr.org/resources/11/librispeech-lexicon.txt

"""

import os
import re

import abkhazia.utils as utils
from abkhazia.prepare import AbstractPreparatorWithCMU


class LibriSpeechPreparator(AbstractPreparatorWithCMU):
    """Convert the LibriSpeech corpus to the abkhazia format"""
    name = 'librispeech'
    description = 'LibriSpeech ASR Corpus'

    long_description = '''
    LibriSpeech is a corpus of approximately 1000 hours of 16kHz read
    English speech, prepared by Vassil Panayotov with the assistance
    of Daniel Povey. The data is derived from read audiobooks from the
    LibriVox project, and has been carefully segmented and
    aligned.'''

    url = ['corpus - http://www.openslr.org/12',
           'dictionary - http://www.openslr.org/11']
    audio_format = 'flac'

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

    def __init__(self, input_dir, log=utils.null_logger(),
                 cmu_dict=None, selection=None, librispeech_dict=None):
        super(LibriSpeechPreparator, self).__init__(input_dir, log=log)

        # guess librispeech dictionary if not specified, look for it
        # in the Librispeech root directory
        if librispeech_dict is None:
            librispeech_dict = os.path.join(
                input_dir, 'librispeech-lexicon.txt')

        # init path to LibriSpeech dictionary
        if not os.path.isfile(librispeech_dict):
            raise IOError(
                'LibriSpeech dictionary does not exist: {}'
                .format(librispeech_dict))
        self.librispeech_dict = librispeech_dict

        # update name, input and output directories if a subpart
        # selection is specified
        if selection is not None:
            self.name += '-' + selection
            self.input_dir = os.path.join(input_dir, selection)

    def list_audio_files(self):
        flacs = utils.list_files_with_extension(
            self.input_dir, '.flac', abspath=True)

        wavs = []
        for flac in flacs:
            utt_id = os.path.basename(flac).replace('.flac', '')
            len_sid = len(utt_id.split('-')[0])  # length of speaker_id
            prefix = '00' if len_sid == 2 else '0' if len_sid == 3 else ''
            wavs.append(prefix + utt_id + '.wav')

        self._wavs = wavs
        return zip(flacs, wavs)

    def make_segment(self):
        segments = dict()
        for wav_file in self._wavs:
            utt_id = os.path.basename(wav_file).replace('.wav', '')
            segments[utt_id] = (utt_id, None, None)
        return segments

    def make_speaker(self):
        utt2spk = dict()
        for wav in self._wavs:
            bname = os.path.basename(wav)
            utt_id = bname.replace('.wav', '')
            speaker_id = bname.split("-")[0]
            utt2spk[utt_id] = speaker_id
        return utt2spk

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
