#!/usr/bin/env python
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

"""Data preparation for the Wall Street Journal corpus"""

import os
import re

import abkhazia.utils as utils
from abkhazia.corpus.prepare import AbstractPreparatorWithCMU


class WallStreetJournalPreparator(AbstractPreparatorWithCMU):
    """Convert the WSJ corpus to the abkhazia format"""

    name = 'wsj'
    description = 'Wall Street Journal ASR Corpus'

    long_description = '''
    The first two CSR Wall Street Journal Corpora (WSJ0 and WSJ1)
    consist primarily of read speech with texts drawn from a
    machine-readable corpus of news text. The texts to be read were
    selected to fall within either a 5,000-word or a 20,000-word
    subset of the WSJ text corpus.'''

    url = ['WSJ0 - https://catalog.ldc.upenn.edu/LDC93S6A',
           'WSJ1 - https://catalog.ldc.upenn.edu/LDC94S13A']
    audio_format = 'sph'

    # IPA transcription of the CMU phones
    exclude_wavs = [
        '4o2x0901','4o6x0901','4o7x0901','4o0x0901',
        '4o3x0901','4o4x0901','4o8x0901','4o9x0901',
        '4o1x0901','4o5x0901','4o2x0b01','4o6x0b01',
        '4o7x0b01','4o0x0b01','4o3x0b01','4o4x0b01',
        '4o8x0b01','4o9x0b01','4o1x0b01','4o5x0b01',
        '4o2x0801','4o6x0801','4o7x0801','4o0x0801',
        '4o3x0801','4o4x0801','4o8x0801','4o9x0801',
        '4o1x0801','4o5x0801','4o2x0a01','4o6x0a01',
        '4o7x0a01','4o0x0a01','4o3x0a01','4o4x0a01',
        '4o8x0a01','4o9x0a01','4o1x0a01','4o5x0a01',
        '4o2x0c01','4o6x0c01','4o7x0c01','4o0x0c01',
        '4o3x0c01','4o4x0c01','4o8x0c01','4o9x0c01',
        '4o1x0c01','4o5x0c01','4o2x0d01','4o6x0d01',
        '4o7x0d01','4o0x0d01','4o3x0d01','4o4x0d01',
        '4o8x0d01','4o9x0d01','4o1x0d01','4o5x0d01',
        '4m5x0201','4m1x0201','4m6x0201','4m7x0201',
        '4m2x0201','4m9x0201','4m0x0201','4m4x0201',
        '4m8x0201','4m3x0201','4o2x0301','4o6x0301',
        '4o7x0301','4o0x0301','4o3x0301','4o4x0301',
        '4o8x0301','4o9x0301','4o1x0301','4o5x0301',
        '4m5x0101','4m1x0101','4m6x0101','4m7x0101',
        '4m2x0101','4m9x0101','4m0x0101','4m4x0101',
        '4m8x0101','4m3x0101','4o2x0201','4o6x0201',
        '4o7x0201','4o0x0201','4o3x0201','4o4x0201',
        '4o8x0201','4o9x0201','4o1x0201','4o5x0201',
        '4oex0701','4odx0701','4ojx0701','4ogx0701',
        '4ocx0701','4oax0701','4ofx0701','4obx0701',
        '4oix0701','4ohx0701','4oex0601','4odx0601',
        '4ojx0601','4ogx0601','4ocx0601','4oax0601',
        '4ofx0601','4obx0601','4oix0601','4ohx0601',
        '4oex0801','4odx0801','4ojx0801','4ogx0801',
        '4ocx0801','4oax0801','4ofx0801','4obx0801',
        '4oix0801','4ohx0801','4oex0901','4odx0901',
        '4ojx0901','4ogx0901','4ocx0901','4oax0901',
        '4ofx0901','4obx0901','4oix0901','4ohx0901',
        '4ojx0j01','4ogx0j01','4oix0j01','4ohx0j01',
        '4oex0201','4odx0201','4ojx0201','4ogx0201',
        '4ocx0201','4oax0201','4ofx0201','4obx0201',
        '4oix0201','4ohx0201','4oex0g01','4odx0g01',
        '4ojx0g01','4ogx0g01','4ocx0g01','4oax0g01',
        '4ofx0g01','4obx0g01','4oix0g01','4ohx0g01',
        '4nix0101','4nix0201','4nmx0201','4nmx0101',
        '4nkx0201','4nkx0101','4nlx0201','4nlx0101',
        '4nnx0201','4nnx0101','4njx0201','4njx0101',
        '4nex0201','4nex0101','4ndx0201','4ndx0101',
        '4nfx0201','4nfx0101','4nhx0101','4nhx0201',
        '4ojx0i01','4ojx0h01','4ogx0i01','4ogx0h01',
        '4oix0h01','4oix0i01','4ohx0h01','4ohx0i01',
        '4oex0501','4odx0501','4ojx0501','4ogx0501',
        '4ocx0501','4oax0501','4ofx0501','4obx0501',
        '4oix0501','4ohx0501','4oex0401','4odx0401',
        '4ojx0401','4ogx0401','4ocx0401','4oax0401',
        '4ofx0401','4obx0401','4oix0401','4ohx0401',
        '4oez0b01','4oez0b04','4oez0b03','4oex0b01',
        '4oez0b02','4odz0b04','4odz0b03','4odz0b02',
        '4odx0b01','4odz0b01','4ojz0b02','4ojx0b01',
        '4ojz0b04','4ojz0b03','4ojz0b01','4ogz0b02',
        '4ogx0b01','4ogz0b03','4ogz0b01','4ogz0b04',
        '4ocz0b04','4ocz0b03','4ocz0b01','4ocx0b01',
        '4ocz0b02','4oaz0b03','4oaz0b02','4oax0b01',
        '4oaz0b04','4oaz0b01','4ofz0b03','4ofz0b04',
        '4ofz0b01','4ofz0b02','4ofx0b01','4obz0b04',
        '4obz0b02','4obx0b01','4obz0b03','4obz0b01',
        '4oix0b01','4oiz0b01','4oiz0b03','4oiz0b02',
        '4oiz0b04','4ohz0b03','4ohx0b01','4ohz0b02',
        '4ohz0b01','4ohz0b04','4oex0d01','4oez0d03',
        '4oez0d04','4oez0d01','4oez0d02','4odz0d04',
        '4odz0d03','4odx0d01','4odz0d02','4odz0d01',
        '4ojz0d04','4ojz0d01','4ojz0d02','4ojx0d01',
        '4ojz0d03','4ogz0d02','4ogz0d04','4ogx0d01',
        '4ogz0d01','4ogz0d03','4ocz0d03','4ocz0d02',
        '4ocz0d01','4ocx0d01','4ocz0d04','4oaz0d02',
        '4oaz0d01','4oaz0d04','4oaz0d03','4oax0d01',
        '4ofx0d01','4ofz0d03','4ofz0d01','4ofz0d04',
        '4ofz0d02','4obz0d01','4obz0d04','4obz0d03',
        '4obx0d01','4obz0d02','4oix0d01','4oiz0d04',
        '4oiz0d03','4oiz0d01','4oiz0d02','4ohz0d02',
        '4ohx0d01','4ohz0d04','4ohz0d03','4ohz0d01',
        '4oez0a03','4oez0a02','4oex0a01','4oez0a01',
        '4oez0a04','4odz0a01','4odz0a02','4odz0a04',
        '4odx0a01','4odz0a03','4ojz0a04','4ojz0a01',
        '4ojz0a02','4ojz0a03','4ojx0a01','4ogx0a01',
        '4ogz0a04','4ogz0a02','4ogz0a01','4ogz0a03',
        '4ocz0a04','4ocz0a01','4ocz0a02','4ocz0a03',
        '4ocx0a01','4oaz0a03','4oaz0a04','4oax0a01',
        '4oaz0a02','4oaz0a01','4ofz0a01','4ofz0a03',
        '4ofz0a04','4ofx0a01','4ofz0a02','4obx0a01',
        '4obz0a04','4obz0a02','4obz0a03','4obz0a01',
        '4oix0a01','4oiz0a03','4oiz0a02','4oiz0a04',
        '4oiz0a01','4ohx0a01','4ohz0a01','4ohz0a02',
        '4ohz0a03','4ohz0a04','4oez0c01','4oex0c01',
        '4oez0c04','4oez0c02','4oez0c03','4odz0c02',
        '4odz0c03','4odz0c04','4odz0c01','4odx0c01',
        '4ojz0c03','4ojz0c01','4ojz0c02','4ojz0c04',
        '4ojx0c01','4ogx0c01','4ogz0c03','4ogz0c04',
        '4ogz0c01','4ogz0c02','4ocz0c01','4ocz0c02',
        '4ocx0c01','4ocz0c03','4ocz0c04','4oaz0c03',
        '4oaz0c01','4oaz0c04','4oax0c01','4oaz0c02',
        '4ofz0c03','4ofz0c01','4ofz0c04','4ofx0c01',
        '4ofz0c02','4obz0c01','4obz0c03','4obz0c04',
        '4obz0c02','4obx0c01','4oiz0c01','4oiz0c04',
        '4oiz0c02','4oix0c01','4oiz0c03','4ohz0c01',
        '4ohz0c03','4ohz0c02','4ohx0c01','4ohz0c04',
        '4oez0e02','4oez0e01','4oez0e03','4oex0e01',
        '4oez0e04','4odz0e03','4odx0e01','4odz0e04',
        '4odz0e01','4odz0e02','4ojz0e03','4ojz0e04',
        '4ojz0e01','4ojz0e02','4ojx0e01','4ogz0e03',
        '4ogz0e04','4ogz0e02','4ogx0e01','4ogz0e01',
        '4ocz0e04','4ocz0e01','4ocx0e01','4ocz0e03',
        '4ocz0e02','4oaz0e04','4oaz0e03','4oaz0e01',
        '4oaz0e02','4oax0e01','4ofz0e01','4ofz0e04',
        '4ofz0e03','4ofz0e02','4ofx0e01','4obz0e01',
        '4obz0e02','4obz0e03','4obx0e01','4obz0e04',
        '4oiz0e04','4oiz0e02','4oiz0e01','4oiz0e03',
        '4oix0e01','4ohz0e01','4ohz0e03','4ohx0e01',
        '4ohz0e04','4ohz0e02','4oez0f04','4oez0f02',
        '4oex0f01','4oez0f03','4oez0f01','4odz0f02',
        '4odz0f01','4odz0f04','4odx0f01','4odz0f03',
        '4ojz0f03','4ojz0f02','4ojx0f01','4ojz0f01',
        '4ojz0f04','4ogz0f01','4ogz0f04','4ogx0f01',
        '4ogz0f02','4ogz0f03','4ocz0f03','4ocz0f02',
        '4ocz0f01','4ocz0f04','4ocx0f01','4oax0f01',
        '4oaz0f02','4oaz0f03','4oaz0f01','4oaz0f04',
        '4ofz0f04','4ofz0f02','4ofz0f01','4ofx0f01',
        '4ofz0f03','4obx0f01','4obz0f01','4obz0f02',
        '4obz0f04','4obz0f03','4oix0f01','4oiz0f04',
        '4oiz0f01','4oiz0f02','4oiz0f03','4ohz0f03',
        '4ohz0f01','4ohx0f01','4ohz0f04','4ohz0f02',
        '4oex0101','4oex0301','4odx0301','4odx0101',
        '4ojx0301','4ojx0101','4ogx0301','4ogx0101',
        '4ocx0101','4ocx0301','4oax0101','4oax0301',
        '4ofx0301','4ofx0101','4obx0101','4obx0301',
        '4oix0101','4oix0301','4ohx0101','4ohx0301',
        '4n5x0201','4n5x0101','4n3x0201','4n3x0101',
        '4n8x0201','4n8x0101','4n9x0101','4n9x0201',
        '4n1x0101','4n1x0201','4n4x0201','4n4x0101',
        '4n0x0201','4n0x0101','4nax0201','4nax0101',
        '4ncx0201','4ncx0101','4nbx0201','4nbx0101',
        '4o2x0101','4o6x0101','4o7x0101','4o0x0101',
        '4o3x0101','4o4x0101','4o8x0101','4o9x0101',
        '4o1x0101','4o5x0101','4o6x0i01','4o7x0i01',
        '4o8x0i01','4o9x0i01','4o2x0e01','4o6x0e01',
        '4o7x0e01','4o0x0e01','4o3x0e01','4o4x0e01',
        '4o8x0e01','4o9x0e01','4o1x0e01','4o5x0e01',
        '4o6x0h01','4o6x0g01','4o6x0f01','4o7x0h01',
        '4o7x0f01','4o7x0g01','4o8x0h01','4o8x0g01',
        '4o8x0f01','4o9x0h01','4o9x0f01','4o9x0g01',
        '4o2x0501','4o6x0501','4o7x0501','4o0x0501',
        '4o3x0501','4o4x0501','4o8x0501','4o9x0501',
        '4o1x0501','4o5x0501','4o2x0401','4o6x0401',
        '4o7x0401','4o0x0401','4o3x0401','4o4x0401',
        '4o8x0401','4o9x0401','4o1x0401','4o5x0401',
        '4o2x0601','4o6x0601','4o7x0601','4o0x0601',
        '4o3x0601','4o4x0601','4o8x0601','4o9x0601',
        '4o1x0601','4o5x0601','4o2x0701','4o6x0701',
        '4o7x0701','4o0x0701','4o3x0701','4o4x0701',
        '4o8x0701','4o9x0701','4o1x0701','4o5x0701',
        '4p7x0101','4p7x0201','4p8x0101','4p8x0201',
        '4p3x0201','4p3x0101','4p6x0101','4p6x0201',
        '4p1x0201','4p1x0101','4p4x0101','4p4x0201',
        '4p9x0101','4p9x0201','4p2x0101','4p2x0201',
        '4p0x0201','4p0x0101','4p5x0101','4p5x0201'
    ]
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
        'R': u'ɹ',
        'W': u'w',
        'Y': u'j',
        'HH': u'h'
    }

    silences = [u"NSN"]  # SPN and SIL will be added automatically

    variants = []  # could use lexical stress variants...

    # those two attribute are None when preparing the whole corpus but
    # redifined for subpart preparation (see classes above)
    file_pattern = None
    directory_pattern = None

    @staticmethod
    def correct_word(word):
        """Return the word with a corrected formating

        Correct the formating of some word or return an empty string to
        indicate that the word should be ignored.

        The corrections applied are:

        * Upcase everything to match the CMU dictionary

        * Remove backslashes (as we don't need the quoting)

        * Normalization for Nov'93 test transcripts (%PERCENT ->
          PERCENT and .POINT -> POINT)

        * the <> means verbal deletion of a word, we just remove
          brackets

        * Other noise indications, e.g. [loud_breath].We replace them
          by the generic <NOISE> marker

        * Replace '--DASH' by '-DASH' to conform with the CMU
          dictionary

        The ignored words (returning an empty string) are:

        * '~' indicates the truncation of an utterance, not a word

        * '.' used to indicate a pause, not included in the transcript
          for now. (could use a special SIL word in the dictionary for
          this)

        * E.g. [<door_slam], this means a door slammed in the
          preceding word. We remove it from the transcript and keep
          the preceding word. (could replace the preceding word by
          <NOISE>)

        * E.g. [door_slam>], this means a door slammed in the next
          word. We remove it from the transcript and keep the next
          word. (could replace the next word by <NOISE>)

        * E.g. [phone_ring/], which indicates the start of this
          phenomenon. We remove it from the transcript and keep the
          part where the phone rings. (could replace the whole part
          where the phone rings by <NOISE>)

        * E.g. [/phone_ring], which indicates the end of this
          phenomenon. We remove it from the transcript and keep the
          part where the phone rings. (could replace the whole part
          where the phone rings by <NOISE>)

        """
        if word == '':
            return ''

        # correct word formating and ignore <> (means verbal deletion)
        word = word.upper()
        word = word.replace('\\', '')
        word = word.replace('%PERCENT', 'PERCENT').replace('.POINT', 'POINT')
        if word[0] == '<' and word[-1] == '>':
            word = word[1:-1]

        # ignore some words
        if(word == '~' or word == '.' or
           (word[:1] == '[<' and word[-1] == ']') or
           (word[0] == '[' and word[-2:] == '>]') or
           (word[0] == '[' and word[-2:] == '/]') or
           (word[:1] == '[/' and word[-1] == ']')):
            return ''

        # correct noise indications
        if word[0] == '[' and word[-1] == ']':
            return '<noise>'

        # This is a common issue: the CMU dictionary has it as -DASH.
        if word == '--DASH':
            return '-DASH'

        # if we reached this point without returning, return w as is
        return word

    def __init__(self, input_dir,
                 log=utils.logger.null_logger(),
                 cmu_dict=None):

        super(WallStreetJournalPreparator, self).__init__(
            input_dir, log=log, cmu_dict=cmu_dict)

        # select only a subpart of recordings and transcriptions.
        # Listing files using the following 2 criterions: 1- files are
        # nested within self.directory_pattern and 2- the 4th letter
        # in the file name is self.file_pattern
        self.log.debug('directory pattern is {}, file pattern is {}'
                       .format(self.directory_pattern, self.file_pattern))

        # setup directory filter
        if self.directory_pattern is None:
            dir_filter = lambda d: True
        else:
            dir_filter = lambda d: d in self.directory_pattern

        # setup file pattern
        if self.file_pattern is None:
            filter_dot = lambda f: f[-4:] == '.dot'
            filter_wv1 = lambda f: f[-4:] == '.wv1'
        else:
            filter_dot = lambda f: (
                f[3] == self.file_pattern and f[-4:] == '.dot')
            filter_wv1 = lambda f: (
                f[3] == self.file_pattern and f[-4:] == '.wv1')

        # filter out the non desired input files
        self.input_recordings = self.filter_files(dir_filter, filter_wv1)
        self.input_transcriptions = self.filter_files(dir_filter, filter_dot)

        self.log.debug('selected {} speech files and {} transcription files'
                       .format(len(self.input_recordings),
                               len(self.input_transcriptions)))

        # filter out the corrupted utterances from input files. The
        # tag '[bad_recording]' in a transcript indicates a problem
        # with the associated recording (if it exists) so exclude it
        self.bad_utts = []
        for trs in self.input_transcriptions:
            for line in utils.open_utf8(trs, 'r').xreadlines():
                if '[bad_recording]' in line:
                    utt_id = re.match(r'(.*) \((.*)\)', line).group(2)
                    self.bad_utts.append(utt_id)

        self.log.debug('found {} corrupted utterances'
                       .format(len(self.bad_utts)))

        # filter out bad utterances
        self.sphs = [sph for sph in self.input_recordings
                     if (os.path.basename(sph).replace('.wv1', '')
                     not in self.bad_utts and
                     os.path.basename(sph).replace('.wv1', '')
                     not in self.exclude_wavs)]

    def filter_files(self, dir_filter, file_filter):
        """Return a list of abspaths to relevant WSJ files"""
        matched = []
        for path, dirs, _ in os.walk(self.input_dir):
            for d in (d for d in dirs if dir_filter(d)):
                for d_path, _, files in os.walk(os.path.join(path, d)):
                    matched += [os.path.join(d_path, f)
                                for f in files if file_filter(f)]

        # TODO when preparing the whole corpus, this function create
        # duplicate entries. Must correct the function (only 1 os.walk
        # needed) instead of this little fix
        return list(set(matched))  # was return matched

    def list_audio_files(self):
        return self.sphs

    def make_segment(self):
        segments = dict()
        for sph in self.sphs:
            utt_id = os.path.splitext(os.path.basename(sph))[0]
            segments[utt_id] = (utt_id, None, None)
        return segments

    def make_speaker(self):
        utt2spk = dict()
        for sph in self.sphs:
            utt_id = os.path.splitext(os.path.basename(sph))[0]
            # speaker_id are the first 3 characters of the filename
            utt2spk[utt_id] = utt_id[:3]
        return utt2spk

    def make_transcription(self):
        # concatenate all the transcription files
        transcription = []

        for trs in self.input_transcriptions:
            transcription += utils.open_utf8(trs, 'r').readlines()

        # parse each line and write it to output file in abkhazia format
        text = dict()
        for line in transcription:
            # parse utt_id and text
            matches = re.match(r'(.*) \((.*)\)', line.strip())
            text_utt = matches.group(1)
            utt_id = matches.group(2)

            # skip bad utterances
            if utt_id not in self.bad_utts:
                # re-format text and remove empty words
                words = [self.correct_word(w) for w in text_utt.split(' ')]

                # output to file
                text[utt_id] = ' '.join([w for w in words if w != ''])
        return text

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
        return lexicon

# TODO check if that's correct (in particular no sd_tr_s or l in WSJ1
# and no si_tr_l in WSJ0 ??)


class JournalistReadPreparator(WallStreetJournalPreparator):
    """Prepare only the journalist read speech from WSJ

    The selected directory pattern is 'si_tr_j' and file pattern is 'c'

    si = speaker-independent (vs sd = speaker-dependent)
    tr = training data
    j = journalist read
    c = common read speech (as opposed to spontaneous, adaptation read)

    """
    name = WallStreetJournalPreparator.name + '-journalist-read'
    directory_pattern = ['si_tr_j']
    file_pattern = 'c'


class JournalistSpontaneousPreparator(WallStreetJournalPreparator):
    """Prepare only the journalist sponaneous speech from WSJ

    The selected directory pattern is 'si_tr_j' and file pattern is 's'

    si = speaker-independent
    tr = training data
    jd = spontaneous journalist dictation
    s = spontaneous no/unspecified verbal punctuation (as opposed to
      common read speech, adaptation read)

    """
    name = WallStreetJournalPreparator.name + '-journalist-spontaneous'
    directory_pattern = ['si_tr_jd']
    file_pattern = 's'


class MainReadPreparator(WallStreetJournalPreparator):
    """Prepare only the read speech from WSJ

    The selected directory pattern are 'si_tr_s', 'si_tr_l',
    'sd_tr_s', 'sd_tr_l' and file pattern is 'c'

    si = speaker-independent
    sd = speaker-dependent
    tr = training data
    s = standard subjects need to read approximately 260 sentences
    l = long sample with more than 1800 read sentences
    c = common read speech as opposed to spontaneous, adaptation read

    """
    name = WallStreetJournalPreparator.name + '-main-read'
    directory_pattern = ['si_tr_s', 'si_tr_l', 'sd_tr_s', 'sd_tr_l']
    file_pattern = 'c'
