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

"""Data preparation for the revised Articulation Index Corpus

Distribution of the revised AIC corpus is freely available at LDC:
https://catalog.ldc.upenn.edu/LDC2015S12. However, you need to be
signed in as an organization to add the corpus to the cart. If you are
an individual, sign up for an account but you need to click on "create
your organization" on the registration page to add your organization
and have administration privileges.
"""

import os
import re

import abkhazia.utils as utils
from abkhazia.corpus.prepare import AbstractPreparatorWithCMU


class AICPreparator(AbstractPreparatorWithCMU):
    """Convert the AIC corpus to the abkhazia format"""
    name = 'aic'
    description = 'Articulation Index Corpus LSCP'

    long_description = '''
    Articulation Index LSCP consists of 20 American English speakers
    (12 males, 8 females) pronouncing syllables. All possible
    Consonant-Vowel (CV) and Vowel-Consonant (VC) combinations were
    recorded for each speaker twice, once in isolation and once within
    a carrier-sentence, for a total of 25768 recorded syllables.'''

    url = 'https://catalog.ldc.upenn.edu/LDC2015S12'

    audio_format = 'flac'

    phones = {
        'a': u'ɑː',
        'xq': u'æ',
        'xa': u'ʌ',
        'c': u'ɔː',
        'xw': u'aʊ',
        'xy': u'aɪ',
        'xr': u'ɝ',
        'xe': u'ɛ',
        'e': u'eɪ',
        'xi': u'ɪ',
        'i': u'iː',
        'o': u'oʊ',
        'xo': u'ɔɪ',
        'xu': u'ʊ',
        'u': u'uː',
        'b': u'b',
        'xc': u'ʧ',
        'd': u'd',
        'xd': u'ð',
        'f': u'f',
        'g': u'g',
        'h': u'h',
        'xj': u'ʤ',
        'k': u'k',
        'l': u'l',
        'm': u'm',
        'n': u'n',
        'xg': u'ŋ',
        'p': u'p',
        'r': u'r',
        's': u's',
        'xs': u'ʃ',
        't': u't',
        'xt': u'θ',
        'v': u'v',
        'w': u'w',
        'y': u'j',
        'z': u'z',
        'xz': u'ʒ',
    }

    silences = [u"NSN"]  # SPN and SIL will be added automatically

    variants = []  # could use lexical stress variants...

    def __init__(self, input_dir,  log=utils.logger.null_logger(), cmu_dict=None):
        super(AICPreparator, self).__init__(
            input_dir, log=log, cmu_dict=cmu_dict)

        self.flacs = utils.list_files_with_extension(
            self.input_dir, '.flac', abspath=True, realpath=True)

        # we need to load the transcriptions here because they are
        # used to compute the lexicon
        normal = os.path.join(self.input_dir, 'data/text/normal.txt')
        weird = os.path.join(self.input_dir, 'data/text/weird.txt')
        self.text = dict()
        for trs in (normal, weird):
            for line in open(trs, 'r'):
                line = line.split(' ')
                self.text[line[0]] = ' '.join(line[1:])

    def list_audio_files(self):
        return self.flacs

    def make_segment(self):
        segments = dict()
        for flac in self.flacs:
            utt_id = os.path.splitext(os.path.basename(flac))[0]
            segments[utt_id] = (utt_id, None, None)
        return segments

    def make_speaker(self):
        utt2spk = dict()
        for flac in self.flacs:
            utt = os.path.splitext(os.path.basename(flac))[0]
            utt2spk[utt] = utt.split('_')[0]
        return utt2spk

    def make_transcription(self):
        return self.text

    def make_lexicon(self):
        lex, oov = self._temp_cmu_lexicon()
        return self._make_lexicon_aux(lex, oov)

    def _load_cmu(self):
        """Return a dict loaded from the CMU dictionay"""
        cmu = {}
        for line in open(self.cmu_dict, "r"):
            match = re.match(r"(.*)\s\s(.*)", line)
            if match:
                entry = match.group(1)
                phn = match.group(2)
                # remove pronunciation variants
                for var in ('0', '1', '2'):
                    phn = phn.replace(var, '')
                # create the combined dictionary
                cmu[entry] = phn
        return cmu

    def _temp_cmu_lexicon(self):
        """Create temp lexicon file and temp OOVs.

        No transcription for the words, we will use the CMU but will
        need to convert to the symbols used in the AIC

        """
        # count word frequencies in text TODO optimize, use
        # collections.Counter
        dict_word = {}
        for k, v in self.text.iteritems():
            matched = re.match(r"([fm0-9]+)_([ps])_(.*?)", k)
            if matched:
                for word in v.upper().split():
                    try:
                        dict_word[word] += 1
                    except KeyError:
                        dict_word[word] = 1

        # create the lexicon by looking up in the CMU dictionary. OOVs
        # should be the sounds and will be written in oov
        lex = dict()
        oov = dict()
        cmu = self._load_cmu()
        for word, freq in dict_word.iteritems():
            try:
                lex[word] = cmu[word]
            except KeyError:
                oov[word] = freq
        return lex, oov

    def _make_lexicon_aux(self, lex, oov):
        """Create the lexicon file, convert from CMU to AC symbols"""
        lexicon = dict()

        for k, v in lex.iteritems():
            word = k.lower()
            phn_trs = self._cmu2aic(v)
            lexicon[word] = phn_trs

        # for the sounds
        for k, v in oov.iteritems():
            # discard the OOV with freq 1 because they are the
            # typos. They will remain OOVs
            if v > 1:
                sound = k.lower()
                # need to split the sound into phones to have the
                # phonetic transcription
                lexicon[sound] = ' '.join(sound.split(":"))

        return lexicon

    @staticmethod
    def _cmu2aic(phn):
        """convert the CMU symbols to AIC symbols in `phn`"""
        for cmu, aic in (
                ('AA', 'a'),
                ('AE', 'xq'),
                ('AH', 'xa'),
                ('AO', 'c'),
                ('AW', 'xw'),
                ('AY', 'xy'),
                ('DH', 'xd'),
                ('EH', 'xe'),
                ('ER', 'xr'),
                ('EY', 'e'),
                ('CH', 'xc'),
                ('HH', 'h'),
                ('IH', 'xi'),
                ('IY', 'i'),
                ('JH', 'xj'),
                ('NG', 'xg'),
                ('OW', 'o'),
                ('OY', 'xo'),
                ('SH', 'xs'),
                ('TH', 'xt'),
                ('UH', 'xu'),
                ('UW', 'u'),
                ('ZH', 'xz'),
                ('D', 'd'),
                ('B', 'b'),
                ('F', 'f'),
                ('G', 'g'),
                ('K', 'k'),
                ('L', 'l'),
                ('M', 'm'),
                ('N', 'n'),
                ('P', 'p'),
                ('R', 'r'),
                ('S', 's'),
                ('T', 't'),
                ('V', 'v'),
                ('W', 'w'),
                ('Y', 'y'),
                ('Z', 'z')):
            phn = phn.replace(cmu, aic)
        return phn
