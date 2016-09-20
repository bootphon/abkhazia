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
"""Data preparation for the CID corpus

For testing
abkhazia prepare cid -v -o ./test_cid


"""

import os
import re

import abkhazia.utils as utils
from abkhazia.corpus.prepare import AbstractPreparator


class CIDPreparator(AbstractPreparator):
    """Convert the CID corpus to the abkhazia format"""

    name = 'cid'
    description = 'Corpus of Interactional Data'

    long_description = '''
    Le CID (Corpus d'interactions dialogales / Corpus of Interactional
    Data) est un corpus audio-video de 8 heures, en français, destiné
    à l'annotation multimodale qui inclut la phonétique, la prosodie,
    la morphologie, la syntaxe, le discours et la mimo-gestualité.
    '''
    url = 'https://www.ortolang.fr/market/corpora/sldr000720'
    audio_format = 'wav'

    # IPA transcriptions for all phones in the CID corpus.
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
        'Z': u'ʒ'
    }

    silences = [u"SIL_WW", u"NSN"]  # SPN and SIL will be added automatically

    variants = []  # could use lexical stress variants...

    def __init__(self, input_dir, log=utils.logger.null_logger(),
                 copy_wavs=False):
        super(CIDPreparator, self).__init__(input_dir, log=log)
        self.copy_wavs = copy_wavs

    def _yield_files(self, pattern):
        """Return files in CID/TextGrid containing 'pattern' in basename"""
        return (t for t in utils.list_directory(
            os.path.join(self.input_dir, 'TextGrid'), abspath=True)
                if pattern in os.path.basename(t))

    @staticmethod
    def _yield_transcription(trs_file):
        """Yield (utt, wav, text, tstart, tstop) read from transcription

        Utterances containing only gpf_* are ignored as they contain
        no clean speech

        """
        # speaker id are the first 2 letters of the file
        spk = os.path.basename(trs_file)[:2]

        utt, tstart, tstop, text = None, None, None, None
        for line in (l.strip() for l in utils.open_utf8(trs_file, 'r')):
            if line.startswith('intervals ['):
                utt = spk + '_' + line.split('[')[1][:-2]
                tstart, tstop = None, None
            elif line.startswith('xmin'):
                tstart = float(line.split(' = ')[1])
            elif line.startswith('xmax'):
                tstop = float(line.split(' = ')[1])
            elif line.startswith('text'):
                text = line.split(' = ')[1].replace('"', '')

            if utt and tstart and tstop and text:
                if not text.startswith('gpf_'):
                    yield utt, spk + '-anonym', text, tstart, tstop
                    utt, tstart, tstop, text = None, None, None, None

    @staticmethod
    def _yield_data(data_file, exclude=[]):
        """Yield (data, tstart, tstop) read from a data file

        data is a string, tstart and tstop are floats.

        The data file can be a 'tokens' or 'phonemes' file, as they
        share the same format, 'data' being a speech token (~ word) or a
        phoneme accordingly.

        The lines before (including) the first occurence of 'dummy'
        are ignored.

        """
        started = False
        data, tstart, tstop = None, None, None
                
        for line in utils.open_utf8(data_file, 'r'):
            # consume lines before the first 'dummy'
            if not started and 'dummy' in line:
                started = True
                continue
            if started:
                if not tstart:
                    tstart = float(line)
                elif not tstop:
                    tstop = float(line)
                else:
                    data = line.replace('"', '').strip()
                    if data not in exclude and not any([r in data for r in exclude]):
                        yield (data, tstart, tstop)
                    data, tstart, tstop = None, None, None

    def list_audio_files(self):
        return utils.list_files_with_extension(
            os.path.join(self.input_dir, 'wav'), '.wav', abspath=True)

    def make_segment(self):
        segments = dict()
        # transcription files are CID/TextGrid/*transcription*.TextGrid
        for trs in self._yield_files('transcription'):
            for utt, wav, _, tstart, tstop in self._yield_transcription(trs):
                segments[utt] = (wav, tstart, tstop)
        return segments

    def make_speaker(self):
        return {k: k[:2] for k in self.make_segment().iterkeys()}

    def make_transcription(self):
        text = dict()

        # transcription files are CID/TextGrid/*transcription*.TextGrid
        for trs_file in self._yield_files('transcription'):
            for utt, _, txt, _, _ in self._yield_transcription(trs_file):
                text[utt] = txt
        return text

    def make_lexicon(self):
        dict_words = dict()
        # iterate on speaker data files
        for ftokens, fphonemes in zip(
                sorted(self._yield_files('tokens')),
                sorted(self._yield_files('phonemes'))):
            yphonemes = self._yield_data(fphonemes, exclude=['+', '#', 'buzz'])
            for word, wstart, wstop in self._yield_data(ftokens, exclude=['+', '#', 'BUZZ', 'buzz']):
                if word not in dict_words:
                    dict_words[word] = []

                phoneme, pstart, pstop = yphonemes.next()
                # if wstart != pstart:
                #     print ("tstart in phonemes and tokens differ in {}: {} {} {} {}"
                #            .format(os.path.basename(ftokens)[:2],
                #                    str(word), str(phoneme), wstart, pstart))


                l = list(phoneme)
                while pstop < wstop:
                    phoneme, pstart, pstop = yphonemes.next()
                    l.append(phoneme)
                dict_words[word].append(l)
        for i in dict_words.keys():
            dict_words[i] = map(list, set(map(tuple, dict_words[i])))
        #print '\n'.join(str(i) for i in dict_words.iteritems())
        import sys
        sys.exit(0)
        return dict_words

    # TODO: fix "spelling" to account for speech errors, etc
    def make_lexicon_old(self):
        dict_word = dict()

        # word files are CID/TextGrid/*tokens*.TextGrid
        for tok_file in self._yield_files('tokens'):
            spk = os.path.basename(tok_file)[:2]
            phon_file = os.path.join(
                self.input_dir, 'TextGrid', spk + "-phonemes.TextGrid")
            token, tstart, tstop = None, None, None
            t1, t2 = 0, 0

            dummy = False
            wd = list()
            phn = list()

            # get word and time intervals
            for line in (l.strip() for l in utils.open_utf8(tok_file, 'r')):
                if dummy is True:
                    line = line.replace('"', '')
                    wd.append(line.encode("utf-8"))
                    if len(wd) == 3:
                        tstart, tstop, token = wd
                        tstart, tstop = float(tstart), float(tstop)
                        wd = list()

                        # find phonetic transcription in phonemes file
                        cnt = 0
                        for pline in (pl.strip() for pl in
                                      utils.open_utf8(phon_file, 'r')):
                            cnt += 1
                            pline = pline.encode("utf-8")
                            if (cnt + 2) % 3 == 0:
                                t1 = pline
                            if (cnt + 1) % 3 == 0:
                                t2 = pline
                            if cnt % 3 == 0:
                                if (str.isdigit(t1.replace(".", "")) and
                                    str.isdigit(t2.replace(".", ""))):
                                    if (tstart <= float(t1) < tstop and
                                        tstart < float(t2) <= tstop):
                                        phn.append(pline.replace('"', ''))
                                else:
                                    phn = list()
                        if token != "#":
                            dict_word[token] = phn  #' '.join(phn)
                            # print tstart, tstop, token, phn
                            # cnt = 0
                else:
                    if '\"dummy\"' in line:
                        dummy = True
        return dict_word
