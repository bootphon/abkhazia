#!/usr/bin/env python
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

"""Data preparation for the Wall Street Journal corpus"""

import os
import re

import abkhazia.utils as utils
from abkhazia.prepare import AbstractPreparatorWithCMU


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

    def __init__(self, input_dir, log=utils.null_logger(), cmu_dict=None):
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
                     if os.path.basename(sph).replace('.wv1', '')
                     not in self.bad_utts]

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
                if not re.match(ur'(.*)\([0-9]+\)$', word):
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
