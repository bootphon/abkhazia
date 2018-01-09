# coding: utf-8

# Copyright 2018 Xuan-Nga Cao, Mathieu Bernard, Adriana Guevara Rukoz
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
"""Data preparation for the Korean Corpus of Spontaneous Speech"""


import codecs
import os
import progressbar
import re
import string as str

import abkhazia.utils as utils
from abkhazia.utils.textgrid import TextGrid
from abkhazia.corpus.prepare import AbstractPreparator


class KCSSPreparator(AbstractPreparator):
    """Convert the KCSS corpus to the abkhazia format"""
    name = 'kcss'

    url = 'http://dx.doi.org/10.13064/KSSS.2015.7.2.103'

    audio_format = 'wav'

    description = 'Korean Corpus of Spontaneous Speech'

    long_description = '''
    The data are freely available to the research community. This
    database consists of 40 hours of sponteaneous speech recorded from
    40 participants. Inspired by the Buckeye corpus.'''

    # Note that both 'pronunciation' and 'orthographic' levels
    # assume the mergers of {ㅔ and ㅐ}, {ㅖ and ㅒ}, and {ㅚ, ㅙ, ㅞ}
    # This can be changed by modifying make_lexicon(self) and the phone list
    phones = {
        'p0': u'p',
        'ph': u'pʰ',
        'pp': u'p*',
        't0': u't',
        'th': u'tʰ',
        'tt': u't*',
        'k0': u'k',
        'kh': u'kʰ',
        'kk': u'k*',
        'll': u'l',
        's0': u's',
        'ss': u's*',
        'hh': u'h',
        'c0': u'ʨ',
        'ch': u'ʨʰ',
        'cc': u'ʨ*',
        'mm': u'm',
        'nn': u'n',
        'ng': u'ŋ',
        'ii': u'i',
        'ye': u'je',
        'ee': u'e',
        'ya': u'ja',
        'aa': u'a',
        'yv': u'jə',
        'xx': u'ɨ',
        'yu': u'ju',
        'vv': u'ə',
        'yo': u'jo',
        'uu': u'u',
        'wi': u'wi',
        'oo': u'o',
        'we': u'we',
        'wa': u'wa',
        'wv': u'wə',
        'xi': u'ɨi'
    }

    # The following phones are specific to the ortographic level.
    # By default, they are considered as separate "phones"
    # This dict can be modified to assign IPA based on the 
    # (1) orthographic cluster or
    # (2) resulting assimilation
    # Please note that further modifications to this script are needed 
    # in order to merge the assimilated clusters to the
    # corresponding phonemes in the "phones" dictionary
    # (e.g., 'ks' => 'k0')
    ortho_phones = {
        'ks': u'ks', # (1) u'ks' (2) u'k'
        'lh': u'lh', # (1) u'lh' (2) u'l'
        'lk': u'lk', # (1) u'lk' (2) u'k'
        'lm': u'lm', # (1) u'lm' (2) u'm'
        'lp': u'lp', # (1) u'lp' (2) u'l'
        'lP': u'lpʰ', # (1) u'lpʰ' (2) u'p'
        'ls': u'ls', # (1) u'ls' (2) u'l'
        'lT': u'ltʰ', # (1) u'ltʰ' (2) u'l'
        'nc': u'nʨ', # (1) u'nʨ' (2) u'n'        
        'nh': u'nh', # (1) u'nh' (2) u'n'
        'ps': u'ps' # (1) u'ps' (2) u'p'
    }

    silences = ['NSN', 'SPN', 'SIL']

    variants = []

    def __init__(self, input_dir,
                 trs_level='pronunciation',
                 extract_alignment=True,
                 log=utils.logger.null_logger()):
        super(KCSSPreparator, self).__init__(input_dir, log=log)

        if trs_level not in ('pronunciation', 'orthographic'):
            raise ValueError(
                'transcription level must be pronunciation or orthographic, '
                'it is: {}'.format(trs_level))

        # add the orthographic specific phones if needed
        if trs_level == 'orthographic':
            self.phones.update(self.ortho_phones)

        self.textgrid = self._load_textgrid(trs_level)

        self.log.info('extracting segments...')
        self.segment = {}
        for utt, grid in self.textgrid.items():
            idx_len = len(str(len(grid['utt'])))

            # extract from TextGrid file the tier that corresponds to
            # the utterance transcription. Use tiers[6] if orthographic
            # utterance transcription (instead of tiers[3]).
            for n, (tstart, tstop, _) in enumerate(grid['utt']):
                idx = str(n+1)
                utt_id = '{}-sent{}'.format(  # -sent001 instead of -sent1
                    utt, '0' * (idx_len - len(idx)) + idx)
                self.segment[utt_id] = (utt, float(tstart), float(tstop))

        self.log.info('extracting transcriptions...')
        bar = progressbar.ProgressBar(max_value=len(self.textgrid.keys()))
        self.transcription = {}
        for i, record in enumerate(self.textgrid.keys()):
            t = self._make_transcription_single(record)
            self.transcription.update(t)
            bar.update(i+1)

        if extract_alignment:
            self.alignment_phones = self.make_alignment(type='phone')
            self.alignment_words = self.make_alignment(type='word')

    def _load_textgrid(self, trs_level):
        """return the TextGrid files in a dict utt_id: textgrid data"""
        # memory optimization: loads only tiers we need (0, 3 and 2
        # for pronunciation, 0, 6 and 5 for orthographic)
        word_idx = 2
        utt_idx = 3
        if trs_level == 'orthographic':
            self.log.info('preparing corpus at orthographic level')
            word_idx += 3
            utt_idx += 3
        else:
            self.log.info('preparing corpus at pronunciation level')

        # build the list of all textgrid files to be parsed
        _dir = os.path.join(self.input_dir, 'label')
        _files = utils.list_files_with_extension(
            _dir, '.TextGrid', abspath=True)
        _name = {f: os.path.splitext(os.path.basename(f))[0] for f in _files}
        self.log.info('loading %s TextGrid files...', len(_name))

        # auxiliary function for parsing a file. Register the files we
        # failed to parse
        _failed = []

        def _load(f):
            try:
                return TextGrid(codecs.open(f, 'r', encoding='utf16').read())
            except IndexError:
                _failed.append(f)

        # parse the textgrid files one per one
        bar = progressbar.ProgressBar(max_value=len(_files))
        textgrid = {}
        for i, f in enumerate(_files):
            loaded = _load(f)
            if loaded:
                textgrid[_name[f]] = {
                    'phone': loaded.tiers[0].simple_transcript,
                    'word': loaded.tiers[word_idx].simple_transcript,
                    'utt': loaded.tiers[utt_idx].simple_transcript}
            bar.update(i+1)

        # report any failed parse
        if _failed:
            self.log.error('failed to parse %s files', len(_failed))
            for f in _failed:
                self.log.debug('failed to parse %s', f)

        return textgrid

    def _make_transcription_single(self, record):
        # collect the utterance boundaries for that record, sorted
        # by increasing tstarts: tuples (tstart, tstop, utt_id)
        tutts = sorted(
            [(v[1], v[2], k)
             for k, v in self.segment.items()
             if v[0] == record])

        # get the word transcript for that record
        word_transcript = [
            (float(t[0]), float(t[1]), t[2])
            for t in self.textgrid[record]['word']]
        nwords = len(word_transcript)

        # read the transcript word per word within each utterance
        # boundaries
        index = 0
        text = {}
        for tstart, tstop, utt_id in tutts:
            words = []
            while index < nwords and word_transcript[index][0] < tstop:
                # get the current word from transcription
                word = word_transcript[index][2]

                # clean it (words like <LAUGH-a b c> have spaces
                # replaced by '_')
                word = word.replace(' ', '_')

                words.append(word)
                index += 1
            text[utt_id] = ' '.join(words).replace('-', '')

        return text

    def list_audio_files(self):
        wav_dir = os.path.join(self.input_dir, 'sounds')
        return utils.list_files_with_extension(wav_dir, '.wav', abspath=True)

    def make_segment(self):
        return self.segment

    def make_speaker(self):
        return {utt_id: utt_id[:3] for utt_id in self.segment.keys()}

    def make_transcription(self):
        return self.transcription

    def make_lexicon(self):
        words = set()
        for utt in self.transcription.values():
            for word in utt.split(' '):
                words.add(word)

        lexicon = {}
        for word in words:
            romanized = re.match("[a-zA-Z0-9]+", word)
            if romanized:
                map = str.maketrans('WEY', 'wey')
                lexicon[word] = ' '.join(re.findall('..?', word)).translate(map)

            else:
                # replace non-speech labels by SPN or NSN
                if re.match('<NOISE.*|<LAUGH>', word):
                    phones = 'NSN'
                elif re.match('<IVER|<VOCNOISE.*|<LAUGH.+|'
                              '<UNKNOWN.*|<PRIVATE.*', word):
                    phones = 'SPN'
                elif word == '<SIL>':
                    phones = 'SIL'
                else:
                    phones = word

                lexicon[word] = phones

        return lexicon

    def make_alignment(self, type='phone'):
        """Extract phones and words alignment from the TextGrid data"""
        self.log.info('extracting %s alignment...', type)
        bar = progressbar.ProgressBar(max_value=len(self.textgrid.keys()))
        alignment = {}
        for i, record in enumerate(self.textgrid.keys()):
            t = self._make_alignment_single(record, type=type)
            alignment.update(t)
            bar.update(i+1)

        return alignment

    def _make_alignment_single(self, record, type='phone'):
        # collect the utterance boundaries for that record, sorted
        # by increasing tstarts: tuples (tstart, tstop, utt_id)
        tutts = sorted(
            [(v[1], v[2], k)
             for k, v in self.segment.items()
             if v[0] == record])

        # get the phone transcript for that record
        transcript = [
            (float(t[0]), float(t[1]), t[2])
            for t in self.textgrid[record][type]]
        ntokens = len(transcript)

        # read the transcript word per word within each utterance
        # boundaries
        index = 0
        alignment = {}
        for tstart, tstop, utt_id in tutts:
            tokens = []
            while index < ntokens and transcript[index][0] < tstop:
                # get the current word from transcription
                t = transcript[index]
                if type == 'word':
                    t = (t[0], t[1], t[2].replace(' ', '_').replace('-', ''))
                tokens.append(t)
                index += 1
            alignment[utt_id] = tokens

        return alignment
