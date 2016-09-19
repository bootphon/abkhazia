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
"""Data preparation for the CID corpus"""

import os
import re

import abkhazia.utils as utils
from abkhazia.corpus.prepare import AbstractPreparator


class CIDPreparator(AbstractPreparator):
    """Convert the CID corpus to the abkhazia format"""

    name = 'cid'
    description = 'Corpus of Interactional Data'

    long_description = '''
    '''

    url = ''
    audio_format = 'wav'

    # IPA transcriptions for all phones in the Buckeye corpus. The
    # following phones are never found in the transcriptions: set([u'own',
    # u'ahn', u'ihn', u'ayn', u'NSN', u'eyn', u'oyn', u'ehn', u'iyn',
    # u'B', u'E', u'uhn', u'aon', u'awn', u'uwn', u'aan', u'ern', u'aen'])
    # Reason: we already collapsed them in the foldings_version
    phones = {
        '@': u'ə',
        'a~': u'ɑ̃',
        'A': u'a',
        'b': u'b',
        'd': u'd',
        'e': u'e',
        'f': u'f',
        'g': u'g',
        'H': u'ɥ',
        'i': u'i',
        'j': u'j',
        'k': u'k',
        'l': u'l',
        'm': u'm',
        'n': u'n',
        'o~': u'ɔ̃',
        'o': u'o',
        'p': u'p',
        'R': u'ʁ',
        's': u's',
        'S': u'ʃ',
        't': u't',
        'u': u'u',
        'U~': u'ɛ̃',
        'v': u'v',
        'w': u'w',
        'y': u'y',
        'z': u'z',
        'Z': u'ʒ',

    }

    silences = [u"SIL_WW", u"NSN"]  # SPN and SIL will be added automatically

    variants = []  # could use lexical stress variants...

    def __init__(self, input_dir, log=utils.logger.null_logger(),
                 copy_wavs=False):
        super(CIDPreparator, self).__init__(input_dir, log=log)
        self.copy_wavs = copy_wavs

    # def _list_files(self, ext, exclude=None, abspath=False, realpath=False):
    #     files = utils.list_files_with_extension(
    #         self.input_dir, ext, abspath=abspath, realpath=realpath)

    #     if exclude is not None:
    #         files = [f for f in files for e in exclude if e not in f]

    #     return files

    def list_audio_files(self):
        pass
        # return self._list_files('.wav', abspath=True, realpath=True)

    def make_segment(self):
        # segments = dict()
        # for utts in self._list_files('.txt', exclude=['readme']):
        #     bname = os.path.basename(utts)
        #     utt = bname.replace('.txt', '')
        #     length_utt = [
        #         len(line.strip().split()) for line in
        #         open(utts, 'r').readlines() if len(line.strip())]

        #     words = utts.replace('txt', 'words_fold')
        #     lines = open(words, 'r').readlines()
        #     del lines[:9]

        #     assert len(lines) == sum(length_utt),\
        #         '{} {}'.format(len(lines), sum(length_utt))

        #     last_offset = '0.000'
        #     current_index = 0
        #     for n in range(len(length_utt)):
        #         onset = last_offset

        #         index_offset = length_utt[n] + current_index
        #         offset_line = lines[index_offset-1]
        #         match_offset = re.match(
        #             r'\s\s+(.*)\s+(121|122)\s(.*)',
        #             offset_line)
        #         if not match_offset:
        #             raise IOError(
        #                 'offset not matched {}'
        #                 .format(offset_line))

        #         offset = match_offset.group(1)

        #         segments[utt + '-sent' + str(n+1)] = (
        #             utt, float(onset), float(offset))

        #         current_index = index_offset
        #         last_offset = offset

        # return segments

    def make_speaker(self):
        pass
        # utt2spk = dict()
        # for utts in self._list_files('.txt', exclude=['readme']):
        #     bname = os.path.basename(utts)
        #     utt = bname.replace('.txt', '')
        #     lines = [l.strip() for l in open(utts, 'r').readlines()
        #              if len(l.strip())]
        #     speaker_id = re.sub(r"[0-9][0-9](a|b)\.txt", "", bname)
        #     for idx, _ in enumerate(lines, start=1):
        #         utt2spk[utt + '-sent' + str(idx)] = speaker_id
        # return utt2spk

    def make_transcription(self):
        pass
        # text = dict()
        # for utts in self._list_files('.txt', exclude=['readme']):
        #     bname = os.path.basename(utts)
        #     utt = os.path.splitext(bname)[0]
        #     for idx, line in enumerate(
        #             (l.strip() for l in open(utts).readlines()
        #              if len(l.strip())), start=1):
        #         text[utt + '-sent' + str(idx)] = line

        # # one utterance have "k p's" in text, where "k p" is an
        # # acronym in this context. Because "p's" is processed as OOV, we
        # # simply replace it by "p"
        # text['s2202b-sent15'] = text['s2202b-sent15'].replace("p's", "p")
        # return text

    def make_lexicon(self):
        pass
        # dict_word = dict()
        # no_trs = set()
        # for utts in self._list_files('.words_fold'):
        #     for line in open(utts, 'r').readlines():
        #         format_match = re.match(
        #             r'\s\s+(.*)\s+(121|122)\s(.*)', line)

        #         if format_match:
        #             word_trs = format_match.group(3)
        #             word_format_match = re.match(
        #                 "(.*); (.*); (.*); (.*)", word_trs)

        #             if word_format_match:
        #                 word = word_format_match.group(1)
        #                 phn_trs = word_format_match.group(3)
        #                 if phn_trs == '':
        #                     no_trs.add(word)
        #                 else:
        #                     dict_word[word] = phn_trs

        # really_no_trs = [t for t in no_trs if t not in dict_word]
        # if really_no_trs:
        #     self.log.debug(
        #         'following words have no transcription in lexicon: {}'
        #         .format(really_no_trs))
        # return dict_word
