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
# along with abkahzia. If not, see <http://www.gnu.org/licenses/>.

"""Data preparation for the revised Buckeye corpus"""

import os
import re

from abkhazia.utils import list_files_with_extension
from abkhazia.prepare import AbstractPreparator

class BuckeyePreparator(AbstractPreparator):
    """Convert the Buckeye corpus to the abkhazia format"""

    name = 'Buckeye'
    description = 'Buckeye Corpus of conversational speech'
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
        'B': u'B',
        'E': u'E',
        'ahn': u'ʌ\u0329',
        'iyn': u'iː\u0329',
        'eyn': u'eɪ\u0329',
        'oyn': u'ɔɪ\u0329',
        'ehn': u'ɛ\u0329',
        'uhn': u'ʊ\u0329',
        'ayn': u'aɪ\u0329',
        'own': u'oʊ\u0329',
        'awn': u'aʊ\u0329',
        'aon': u'ɔː\u0329',
        'aan': u'ɑː\u0329',
        'ihn': u'ɪ\u0329',
        'ern': u'ɝ\u0329',
        'uwn': u'uː\u0329',
        'aen': u'æ\u0329',
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

    def list_audio_files(self):
        wavs = list_files_with_extension(self.input_dir, '.wav', abspath=True)
        return wavs, [os.path.basename(w) for w in wavs]

    # TODO function too big, refactor
    def make_segment(self):
        utt_dir = os.path.join(self.input_dir, 'txt')
        wrd_dir = os.path.join(self.input_dir, 'words_fold')

        outfile = open(self.segments_file, "w")
        for utts in list_files_with_extension(utt_dir, '.txt'):
            length_utt = []
            with open(utts) as infile_txt:
                current_index = 0
                last_offset = 0
                lines = infile_txt.readlines()
                bname = os.path.basename(utts)
                bname_word = bname.replace('txt', 'words')
                bname_wav = bname.replace('txt', 'wav')
                utt = bname.replace('.txt', '')
                length_utt = [len(line.strip().split()) for line in lines]
                wrd = os.path.join(wrd_dir, bname_word)
                with open(wrd) as infile_wrd:
                    lines_2 = infile_wrd.readlines()
                    #print (wrd)
                    del lines_2[:9]
                    assert len(lines_2) == sum(length_utt),\
                        '{} {}'.format(len(lines_2), sum(length_utt))
                    for n in range(len(length_utt)):
                        if n == 0:
                            onset = '0.000'
                            outfile.write(utt + '-sent' +
                                          str(n+1) + ' ' +
                                          bname_wav + ' ' +
                                          onset + ' ')

                            index_offset = length_utt[n]
                            offset_line = lines_2[index_offset-1]

                            match_offset = re.match(
                                r'\s\s+(.*)\s+(121|122)\s(.*)', offset_line)
                            if not match_offset:
                                raise IOError('offset line unmatched: {}'
                                              .format(offset_line))

                            offset = match_offset.group(1)
                            outfile.write(str(offset))
                            current_index = index_offset
                            last_offset = offset
                            outfile.write('\n')
                        else:
                            onset = last_offset
                            outfile.write(utt + '-sent' +
                                          str(n+1) + ' ' +
                                          bname_wav + ' ' +
                                          str(onset) + ' ')

                            index_offset = length_utt[n]+current_index
                            offset_line = lines_2[index_offset-1]
                            match_offset = re.match(
                                r'\s\s+(.*)\s+(121|122)\s(.*)', offset_line)
                            if not match_offset:
                                raise IOError(
                                    'offset not matched {}'.format(offset_line))

                            offset = match_offset.group(1)
                            outfile.write(str(offset))
                            current_index = index_offset
                            last_offset = offset
                            outfile.write('\n')
        self.log.debug('finished creating segments file')

    def make_speaker(self):
        utt_dir = os.path.join(self.input_dir, 'txt')

        outfile = open(self.speaker_file, "w")
        for utts in list_files_with_extension(utt_dir, '.txt'):
            with open(utts) as infile_txt:
                lines = infile_txt.readlines()
                bname = os.path.basename(utts)
                utt = bname.replace('.txt', '')
                speaker_id = re.sub(r"[0-9][0-9](a|b)\.txt", "", bname)
                for idx, _ in enumerate(lines, start=1):
                    outfile.write(utt + '-sent' + str(idx)
                                  + ' ' + speaker_id + '\n')

        self.log.debug('finished creating utt2spk file')

    def make_transcription(self):
        utt_dir = os.path.join(self.input_dir, 'txt')

        outfile = open(self.transcription_file, "w")
        for utts in list_files_with_extension(utt_dir, '.txt'):
            with open(utts) as infile_txt:
                lines = infile_txt.readlines()
                bname = os.path.basename(utts)
                utt = bname.replace('.txt', '')
                for idx, val in enumerate(lines, start=1):
                    outfile.write(utt + '-sent' + str(idx) + ' ')
                    words = val.split()
                    if len(words) > 1:
                        for word in words[:-1]:
                            outfile.write(word + ' ')
                        outfile.write(str(words[-1]) + '\n')
                    else:
                        for word in words:
                            outfile.write(word)
                        outfile.write('\n')
        self.log.debug('finished creating text file')

    def make_lexicon(self):
        wrd_dir = os.path.join(self.input_dir, 'words_fold')

        dict_word = {}
        outfile = open(self.lexicon_file, "w")
        for utts in list_files_with_extension(wrd_dir, '.words'):
            with open(utts) as infile_txt:
                # for each line of transcription, store the words in a
                # dictionary and increase frequency
                lines = infile_txt.readlines()
                for line in lines:
                    line.strip()
                    format_match = re.match(
                        r'\s\s+(.*)\s+(121|122)\s(.*)', line)

                    if format_match:
                        word_trs = format_match.group(3)
                        word_format_match = re.match(
                            "(.*); (.*); (.*); (.*)", word_trs)

                        if word_format_match:
                            word = word_format_match.group(1)
                            phn_trs = word_format_match.group(3)
                            # TODO what is that ? a comment ? a legacy code ?
                            # Doing some foldings for spoken noise"
                            # pattern1 = re.compile("<UNK(.*)")
                            # if pattern1.match(word):
                            #     phn_trs = phn_trs.replace('UNKNOWN', 'SPN')
                            # pattern2 = re.compile("<(CUT|cut)(.*)")
                            # if pattern2.match(word):
                            #     phn_trs = phn_trs.replace('CUTOFF', 'SPN')
                            # pattern3 = re.compile("<LAU(.*)")
                            # if pattern3.match(word):
                            #     phn_trs = phn_trs.replace('LAUGH', 'SPN')
                            # pattern4 = re.compile("<(EXT|EXt)(.*)")
                            # if pattern4.match(word):
                            #     phn_trs = phn_trs.replace('LENGTH_TAG', 'SPN')
                            # pattern5 = re.compile("<ERR(.*)")
                            # if pattern5.match(word):
                            #     phn_trs = phn_trs.replace('ERROR', 'SPN')
                            # pattern6 = re.compile("<HES(.*)")
                            # if pattern6.match(word):
                            # phn_trs = phn_trs.replace('HESITATION_TAG', 'SPN')
                            # pattern7 = re.compile("<EXCL(.*)")
                            # if pattern7.match(word):
                            #     phn_trs = phn_trs.replace('EXCLUDE', 'SPN')

                            if word not in dict_word:
                                dict_word[word] = phn_trs

        for word, freq in sorted(
                dict_word.items(), key=lambda kv: kv[1], reverse=True):
            outfile.write(word + ' ' + freq + '\n')

        self.log.debug('finished creating lexicon file')
