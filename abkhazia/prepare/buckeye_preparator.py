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
"""Data preparation for the revised Buckeye corpus"""

import os
import re

import abkhazia.utils as utils
from abkhazia.prepare import AbstractPreparator


class BuckeyePreparator(AbstractPreparator):
    """Convert the Buckeye corpus to the abkhazia format"""

    name = 'buckeye'
    description = 'Buckeye Corpus of conversational speech'

    long_description = '''
    The Buckeye Corpus of conversational speech contains high-quality
    recordings from 40 speakers in Columbus OH conversing freely with
    an interviewer. The speech has been orthographically transcribed
    and phonetically labeled. The audio and text files, together with
    time-aligned phonetic labels, are stored in a format for use with
    speech analysis software (Xwaves and Wavesurfer). Software for
    searching the transcription files is currently being written. The
    corpus is FREE for noncommercial uses.

    This project is funded by the National Institute on Deafness and
    other Communication Disorders and the Office of Research at Ohio
    State University.'''

    url = 'http://buckeyecorpus.osu.edu'
    audio_format = 'wav'

    # IPA transcriptions for all phones in the Buckeye corpus. The
    # following phones are never found in the transcriptions: set([u'own',
    # u'ahn', u'ihn', u'ayn', u'NSN', u'eyn', u'oyn', u'ehn', u'iyn',
    # u'B', u'E', u'uhn', u'aon', u'awn', u'uwn', u'aan', u'ern', u'aen'])
    # Reason: we already collapsed them in the foldings_version
    phones = {
        'iy': u'iː',
        'ih': u'ɪ',
        'eh': u'ɛ',
        'ey': u'eɪ',
        'ae': u'æ',
        'aa': u'ɑː',
        'aw': u'aʊ',
        'ay': u'aɪ',
        'ah': u'ʌ',
        'ao': u'ɔː',
        'oy': u'ɔɪ',
        'ow': u'oʊ',
        'uh': u'ʊ',
        'uw': u'uː',
        'er': u'ɝ',
        'jh': u'ʤ',
        'ch': u'ʧ',
        'b': u'b',
        'd': u'd',
        'g': u'g',
        'p': u'p',
        't': u't',
        'k': u'k',
        'dx': u'ɾ',
        's': u's',
        'sh': u'ʃ',
        'z': u'z',
        'zh': u'ʒ',
        'f': u'f',
        'th': u'θ',
        'v': u'v',
        'dh': u'ð',
        'm': u'm',
        'n': u'n',
        'ng': u'ŋ',
        'em': u'm\u0329',
        'nx': u'ɾ\u0303',
        'en': u'n\u0329',
        'eng': u'ŋ\u0329',
        'l': u'l',
        'r': u'r',
        'w': u'w',
        'y': u'j',
        'hh': u'h',
        'el': u'l\u0329',
        'tq': u'ʔ',
        # 'B': u'B',
        # 'E': u'E',
        # 'ahn': u'ʌ\u0329',
        # 'iyn': u'iː\u0329',
        # 'eyn': u'eɪ\u0329',
        # 'oyn': u'ɔɪ\u0329',
        # 'ehn': u'ɛ\u0329',
        # 'uhn': u'ʊ\u0329',
        # 'ayn': u'aɪ\u0329',
        # 'own': u'oʊ\u0329',
        # 'awn': u'aʊ\u0329',
        # 'aon': u'ɔː\u0329',
        # 'aan': u'ɑː\u0329',
        # 'ihn': u'ɪ\u0329',
        # 'ern': u'ɝ\u0329',
        # 'uwn': u'uː\u0329',
        # 'aen': u'æ\u0329',
        '{B_TRANS}': u'{B_TRANS}',
        '{E_TRANS}': u'{E_TRANS}',
        'CUTOFF': u'CUTOFF',
        'ERROR': u'ERROR',
        'EXCLUDE': u'EXCLUDE',
        'UNKNOWN_WW': u'UNKNOWN_WW',
        'UNKNOWN': u'UNKNOWN',
        'VOCNOISE': u'VOCNOISE',
        'HESITATION_TAG': u'HESITATION_TAG',
        'LENGTH_TAG': u'LENGTH_TAG',
        'VOCNOISE_WW': u'VOCNOISE_WW',
        'NOISE': u'NOISE',
        'NOISE_WW': u'NOISE_WW',
        'IVER': u'IVER',
        'LAUGH': u'LAUGH',
    }

    silences = [u"SIL_WW", u"NSN"]  # SPN and SIL will be added automatically

    variants = []  # could use lexical stress variants...

    def __init__(self, input_dir, log=utils.null_logger(), copy_wavs=False):
        super(BuckeyePreparator, self).__init__(input_dir, log=log)
        self.copy_wavs = copy_wavs

    def _list_files(self, ext, exclude=None, abspath=False, realpath=False):
        files = utils.list_files_with_extension(
            self.input_dir, ext, abspath=abspath, realpath=realpath)

        if exclude is not None:
            files = [f for f in files for e in exclude if e not in f]

        return files

    def list_audio_files(self):
        return self._list_files('.wav', abspath=True, realpath=True)

    def make_segment(self):
        segments = dict()
        for utts in self._list_files('.txt', exclude=['readme']):
            bname = os.path.basename(utts)
            utt = bname.replace('.txt', '')
            length_utt = [
                len(line.strip().split()) for line in
                open(utts, 'r').readlines() if len(line.strip())]

            words = utts.replace('txt', 'words_fold')
            lines = open(words, 'r').readlines()
            del lines[:9]

            assert len(lines) == sum(length_utt),\
                '{} {}'.format(len(lines), sum(length_utt))

            last_offset = '0.000'
            current_index = 0
            for n in range(len(length_utt)):
                onset = last_offset

                index_offset = length_utt[n] + current_index
                offset_line = lines[index_offset-1]
                match_offset = re.match(
                    r'\s\s+(.*)\s+(121|122)\s(.*)',
                    offset_line)
                if not match_offset:
                    raise IOError(
                        'offset not matched {}'
                        .format(offset_line))

                offset = match_offset.group(1)

                segments[utt + '-sent' + str(n+1)] = (
                    utt, str(onset), str(offset))

                current_index = index_offset
                last_offset = offset

        return segments

    def make_speaker(self):
        utt2spk = dict()
        for utts in self._list_files('.txt', exclude=['readme']):
            bname = os.path.basename(utts)
            utt = bname.replace('.txt', '')
            lines = [l.strip() for l in open(utts, 'r').readlines()
                     if len(l.strip())]
            speaker_id = re.sub(r"[0-9][0-9](a|b)\.txt", "", bname)
            for idx, _ in enumerate(lines, start=1):
                utt2spk[utt + '-sent' + str(idx)] = speaker_id
        return utt2spk

    def make_transcription(self):
        text = dict()
        for utts in self._list_files('.txt', exclude=['readme']):
            bname = os.path.basename(utts)
            utt = os.path.splitext(bname)[0]
            for idx, line in enumerate(
                    (l.strip() for l in open(utts).readlines()
                     if len(l.strip())), start=1):
                text[utt + '-sent' + str(idx)] = line
        return text

    def make_lexicon(self):
        dict_word = dict()
        no_trs = set()
        for utts in self._list_files('.words_fold'):
            for line in open(utts, 'r').readlines():
                format_match = re.match(
                    r'\s\s+(.*)\s+(121|122)\s(.*)', line)

                if format_match:
                    word_trs = format_match.group(3)
                    word_format_match = re.match(
                        "(.*); (.*); (.*); (.*)", word_trs)

                    if word_format_match:
                        word = word_format_match.group(1)
                        phn_trs = word_format_match.group(3)
                        if phn_trs == '':
                            no_trs.add(word)
                        else:
                            dict_word[word] = phn_trs
        if no_trs:
            self.log.debug(
                'following words have no transcription in lexicon: {}'
                .format(no_trs))
        return dict_word
