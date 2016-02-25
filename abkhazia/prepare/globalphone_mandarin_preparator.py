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

"""Mandarin specific preprocessing for the GlobalPhone corpus

Caveats:
-------

- Speakers have regional accents: this limits the detail into which
  one can go for phonological or linguistic analysis based on this
  corpus

- Dictionary has a lot of entries... supposed to be constructed from
  text, so why much of it is not used? Maybe it was built with the
  larger corpus of text used for Language Model generation?  We need
  to ask this to the corpus builders.

- Word units do not correspond to actual words, whatever this might
  means in Mandarin (e.g. 'notsure' could be a word in English with
  this approach)

Mismatched audio and transcripts:
---------------------------------

speaker 84 seems all mixed up, list of main defects found:

    audio 100 -> transcription 102
    audio 102 -> transcription 10
    audio 104 -> transcription 108
    audio 105 -> transcription 107
    audio 107 -> transcription 100
    audio 108 -> transcription 105
    audio 109 -> transcription 104
    audio 110 -> transcription 11
    audio 111 -> transcription 116
    audio 112 -> transcription 115
    audio 113 -> transcription 114
    audio 114 -> transcription 110
    audio 115 -> transcription 113
    audio 116 -> transcription 112
    audio 10 -> no corresponding transcript?
    audio 11 -> no corresponding transcript?

there are also two audio files (103 and 117) with no associated
transcript maybe one correspond to transcription 111, which does not
seem to be associated to any other audio

speaker 63 utterance 10????
speaker 64 utterance 10????

And probably many more...

OOV:
----

They are not really OOV, only some transcripts contain the correct
sentence plus a part of it that has been duplicated for some
reason. In general, the duplicated part is pasted first, then the
correct full sentence is concatenated to it without point or spaces,
yielding the OOV items as a concatenation of the last word of the
fragment and the first word of the sentence.

There is only one OOV item not conforming to this pattern:
tong3yi1zhan4xian4zhan4xian4, where the actual word is
'tong3yi1zhan4xian4' but the speaker hesitated between yi1 and
zhan4xian4. For this utterance, see what has been done for other
sentences with hesitations and do the same (either ignore it and
transcribe as tong3yi1zhan4xian4 or throw away the utterance?).

List of oov word types with occurences counts:

Counter({
    u'yun3deng3': 1,
    # need to remove begginning + this one has in addition a bad
    # transcription 'hai2you3 hai2you3 hai2you3 yu2 dui4 yun3 yun3'
    # which does not match the audio file

    u'tong3yi1zhan4xian4zhan4xian4': 1,
    # need to remove begginning

    u'xing4ju4liao3jie3': 1,
    # need to remove beginning
    # (ju4liao3jie3 wei2 jia1qiang2 liang2 you2 shi4chang3 de5
    # hong2guan1 diao4 kong4 guo2wu4yuan4 qu4nian2 jue2ding4
    # liang2shi5 qi3ye4 de5 zheng4ce4 xing4)

    u'tong3yi1zhan4xian4ta1': 1,
    # not the same problem (see above) but in the same sentence
    # as another OOV
})

Homophones:
-----------

All homophones seem similar to the following pair: xin1i2/xin1yi2 Not
a lot of them in the dictionary and none actually occuring in the text
so we just ignore them for now (see data_validation.py log for a
detailed account)

TODO:
-----

Detect potential defective transcripts:

1. look for very unlikely sentences with kaldi and see whether this
   way we can reliably detect the oov utterances and the utterances
   with known transcription problems

2. look for transcriptions which contain a long substring that is
   repeated (find longest repeating substring or longest matching
   substring with edit distance lower than xxx) (removing all spaces
   from the transcription) and check that we find the oov sentences
   this way

3. have somebody read the transcript and simultaneously listen to the
   audio and note every mismatch) Then have somebody check and correct
   the problematic transcripts

"""

import tempfile
import os

from abkhazia.utils import open_utf8
from abkhazia.prepare.globalphone_abstract_preparator import (
    AbstractGlobalPhonePreparator)

class MandarinPreparator(AbstractGlobalPhonePreparator):
    """Mandarin specific preprocessing for the GlobalPhone corpus"""
    language = 'Mandarin'

    name = '-'.join([AbstractGlobalPhonePreparator.name, language]).lower()

    transcription_key = 'rmn'

    # all these files are empty in the original GlobalPhone Mandarin
    # distribution there is also no transcription corresponding to
    # these files
    corrupted_wavs = [
        'CH046_34', 'CH046_35', 'CH046_36', 'CH046_37',
        'CH046_38', 'CH046_39', 'CH046_40', 'CH046_41',
        'CH046_42', 'CH046_43', 'CH046_44', 'CH046_45',
        'CH046_46', 'CH046_47', 'CH046_48', 'CH046_49',
        'CH046_50', 'CH046_51', 'CH046_52', 'CH046_53',
        'CH046_54', 'CH046_55', 'CH046_56', 'CH046_57',
        'CH046_58', 'CH046_59', 'CH046_60', 'CH046_61',
        'CH046_62', 'CH046_63', 'CH046_64', 'CH046_65',
        'CH046_66', 'CH046_67', 'CH046_68', 'CH046_69',
        'CH046_70', 'CH046_71', 'CH046_72', 'CH046_73',
        'CH046_74', 'CH046_75', 'CH046_76', 'CH046_77']

    # there are wavefiles for these utterances, but no transcription
    missing_transcripts = [
        'CH025_76', 'CH025_77', 'CH025_78', 'CH025_79',
        'CH073_119', 'CH073_118', 'CH073_62', 'CH084_117',
        'CH073_117', 'CH076_103', 'CH073_63', 'CH025_90',
        'CH025_91', 'CH025_92', 'CH091_43', 'CH064_128',
        'CH084_103', 'CH063_121', 'CH051_81', 'CH076_116',
        'CH076_117', 'CH025_89', 'CH025_88', 'CH025_83',
        'CH025_82', 'CH025_81', 'CH025_80', 'CH025_87',
        'CH025_86', 'CH025_85', 'CH025_84']

    exclude_wavs = corrupted_wavs + missing_transcripts

    # Main sources:
    #    http://talkbank.org/pinyin/Trad_chart_IPA.php
    #    http://en.wikipedia.org/wiki/Pinyin#Overview
    #
    # See also:
    #    http://ling.cass.cn/yuyin/english/sampac/sampac.htm
    #    http://en.wikipedia.org/wiki/Standard_Chinese_phonology#Palatal_series
    #
    # GP_Mandarin includes the palatal series in its phoneset, but
    # the glide series is integrated into the vowels
    #
    # TODO articulatory features, closest UPSID match and stats
    vowels = {
        'a': u'ä',
        'e': u'ə',
        'i': u'i',
        'ii': u'ɨ',
        'o': u'ɤ',
        'u': u'u',
        'v': u'y',
        'ai': u'aɪ',
        'ao': u'ɑʊ',
        'ei': u'eɪ',
        'ia': u'iä',
        'ie': u'iɛ',
        'io': u'iʊ',
        # according to the sources above: 'iu' should be completely folded
        # with 'iou'...
        'iu': u'iu',
        'ou': u'oʊ',
        'ua': u'uä',
        # here the two sources above disagree with GP who proposes 'uɛ'
        'ue': u'uə',
        # discrepancy here too... but not sure what GP proposition is due
        # to font issues in pdf
        'uo': u'uɔ',
        'iao': u'iɑʊ',
        'uai': u'uaɪ',
        # here too GP proposes 'uɛi' I think
        'uei': u'ueɪ',
        # 4 tone vowel: never happens with tone 5
        'va': u'yɛ',
        # 4 tone vowel: never happens with tone 5
        've': u'yœ',
        # here GP proposes iʊu; 4 tone vowel: never happens with tone 5
        'iou': u'ioʊ'
    }

    # no glides (j, w and ɥ) in the GP version (they are in the vowels)
    # meaning that many of the diphtongs and triphtongs could have an
    # alternative translation with a glide at the beginning as in
    # http://talkbank.org/pinyin/Trad_chart_IPA.php
    consonants = {
        'b': u'p',
        'c': u'tsʰ',
        'ch': u'tʂʰ',
        'd': u't',
        'f': u'f',
        'g': u'k',
        'h': u'x',
        'j': u'tɕ',
        'k': u'kʰ',
        'l': u'l',
        'm': u'm',
        'n': u'n',
        'ng': u'ŋ',
        'p': u'pʰ',
        'q': u'tɕʰ',
        'r': u'ɻ',
        # a common alternative is ʐ: the only difference is in the manner
        # of articulation:
        # ʐ is a sibilant fricative
        # ɻ is an approximant
        's': u's',
        'sh': u'ʂ',
        't': u'tʰ',
        'x': u'ɕ',
        'z': u'ts',
        'zh': u'tʂ'
    }

    # source for IPA notation:
    # https://en.wikipedia.org/wiki/Tone_%28linguistics%29#Phonetic_notation
    tones = [
        ('1', u'˥'),
        ('2', u'˧˥'),
        ('3', u'˨˩˦'),
        ('4', u'˥˩'),
        ('5', u'˧')  # mid-level neutral
    ]

    four_tones_vowels = ['va', 've', 'iou']

    # generate dict associating phones with ipa and tonal variants
    variants = []
    phones = consonants
    for vowel, ipa in vowels.iteritems():
        l_tones = tones[:-1] if vowel in four_tones_vowels else tones
        for tone, ipa_t in l_tones:
            tonal = vowel + tone
            assert tonal not in phones
            phones[tonal] = ipa + ipa_t

        variants.append([vowel + tone for tone, _ in l_tones])

    def correct_dictionary(self):
        """Correct problems with the GlobalPhone Mandarin dictionary

        The corrections are completely ad hoc the result is stored in
        a temporary file

        """
        self.log.info('Correcting dictionary')

        # the following words are in the dictionary but are not used
        # in the transcriptions they will be dropped
        words_to_drop = [u'#fragment#', u'#noise#', u'$', u'(', u')', u'SIL']

        # correct content
        correct_lines = []
        for line in open_utf8(self.dictionary, 'r').xreadlines():
            if all([not(u'{'+word+u'}' in line) for word in words_to_drop]):
                line = line.replace(u'{lai2zhe3bu2ju4 }', u'{lai2zhe3bu2ju4}')
                correct_lines.append(line)

        # update self.dictionary with the corrected content
        fid, filename = tempfile.mkstemp()
        os.close(fid)
        with open_utf8(filename, 'w') as out:
            for line in correct_lines:
                out.write(line)

        self.log.info('Dictionary corrected, writed in {}'.format(filename))
        self.dictionary = filename
        return True
