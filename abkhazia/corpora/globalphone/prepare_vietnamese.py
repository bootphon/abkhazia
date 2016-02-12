# -*- coding: utf-8 -*-
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

"""Vietnamese specific preprocessing for the GlobalPhone corpus

Caveats:
--------

- clipping problems in certain wavefiles

- for now we use a lexicon of monosyllables (see below) correspond to
  linguistic structure, but not appropriate for ASR...

- the dictionary is considerably smaller than that from Mandarin for
  some reason, even with the polysyllable artificial constructs

Transcript and lexicon problems:
--------------------------------

* Multisyllabic units:

Starting from speaker 200 till last speaker 208 seem to not have been
prepared like the rest of the transcriptions (supplementary speaker
for phone variety?).

Many double spacings in text and also same speakers have '_' linking
some words.  The '_' indicates multisyllabic compounds that actually
are not really words but are useful for ASR. These compounds are in
the dictionary, however they are not in the transcription for the main
set of speakers (before speaker 200).

- We could try to parse the transcription with the dictionary, but
  there might be some ambiguities.

- Before that, we should ask for the original from the authors or get
  confirmation that they are not useful for training, only for
  recognition, in which case having them in the lexicon is enough,
  although it means that we will have to remove the '_' from the
  produced transcripts to measure the performance and we will only
  have performance on monosyllables (and we can actually check whether
  having kept the '_' in lexicon makes any difference)

- For now, we just get rid of the transcription '_'.  Should we also
 remove those entries from the lexicon? W -> We should try both and
 checks that keeping them increase performance on monosyllables (see
 discussion above)


* Other problems:

- There are transcriptions for alphabet letters that are very weird
  (e.g. letter K transcribed as k instead of ka or something else with
  a vowel), the secondary transcriptions often as 'j' for these
  letters also seem weird.

- Also there seem to be homophonic transcription for uppercase and
  lowercase version of some word... Is that because one is a proper
  name? Otherwise we should get rid of it both in dictionary and text
  (some do occur in text such as À/à or A/a; see remarks on homophones
  below)

- Proper names are not transcribed in the Dict although there is quite
  a lot of them in the text (see data_validation.py log for a complete
  list of OOV items)


Homophones:
-----------

Homophones will impair WER measures for no good reason, in particular
when using a simple loop language model, so we might get rid of them,
although this might cause problem when using the language models
compiled for the original dictionary (but we might have to change
these because of the changes we already introduced anyway)

Example of homophones: loại/lọai, dao/giao, and many more...

Quite a few occuring in text and sometimes seem bad (lowercase and
uppercase versions for example) Note that transcribing proper names
might add some more homophones On the other hand using multisyllabic
word units might reduce the number of actual occurences of homophic
pairs in the corpus (see data_validation.py log for a detailed
account)


Alternative pronunciations:
---------------------------

In the Vietnamese dictionary alternative pronunciations are supplied
for certain words, but they are not explicitly used in the text there
are never more than two version of a given word

For now we simply drop them

Note that kaldi can accomodate alternative pronunciation and even
pronunciation probabilities without problems, but using them in ABX
would be bothersome

One possibility to accomodate several pronunciation would be to have
an optional lexicon_with_variants.txt file, optionally also with
probabilities that would be used by kaldi Then one could either ignore
the variants in ABX or use the kaldi acoustic models to do a hard
assignment of each occurence of each word to a given pronunciation

Here we make the assumption that the first pronunciation (without the
(2) suffix) is the more likely. We could check this assumption by
comparing WERs with first or second variant or both

"""

import tempfile
import os
import re

from abkhazia import utils
from abkhazia.corpora.globalphone import AbstractGlobalPhonePreparator


class VietnamesePreparator(AbstractGlobalPhonePreparator):
    """Vietnamese specific preprocessing for the GlobalPhone corpus"""
    language = 'Vietnamese'

    name = '-'.join([AbstractGlobalPhonePreparator.name, language])

    transcription_key = 'trl'


    # Which vowels are observed with which tones? The only unobserved
    # combinations are uou_5 and eu_1
    #
    # Main source:
    #	GP documentation
    #
    # Other sources:
    #	https://en.wikipedia.org/wiki/Vietnamese_phonology
    #	https://en.wikipedia.org/wiki/Tone_%28linguistics%29#Phonetic_notation
    #	http://en.wikipedia.org/wiki/Vietnamese_alphabet
    #
    # Main source for vowels only:
    #   https://en.wikipedia.org/wiki/Vietnamese_phonology except for ɨ/ɯ,
    # following:
    # http://www.academia.edu/1972509/Vietnamese_Hanoi_Vietnamese_
    #
    # Note diphtongs are often presented as vowel+glide, we followed
    # GP choice of vowel+vowel
    #
    # For vowel length we have normal and extra-short (is it maybe
    # long and short?)
    # TODO articulatory features, closest UPSID match and stats

    # a1 and a2 are exchanged in the GP handout!!! (as seen by
    # looking into the dict).
    vowels = {
        # short a: sometimes for both a and schwa: the length
        # contrasts are reported as /a/: /a:/
        'a2': u'ă',
        # both a's are sometimes reported as more centralized...
        'a1': u'a',
        # short schwa
        'a3': u'ə\u0306',
        'e1': u'ɛ',
        'e2': u'e',
        'i': u'i',
        'o1': u'ɔ',
        'o2': u'o',
        # sometimes reported as əː long version of u'ə'
        'o3': u'ɤː',
        'u1': u'u',
        # sometimes reported as ɯ
        'u2': u'ɨ',
        'ai': u'ai',
        # why not au?
        'ao': u'aʊ',
        # why not ău?
        'au': u'ăʊ',
        'au3': u'ə\u0306ʊ',
        'ay': u'ăi',
        'ay3': u'ə\u0306i',
        'eo': u'ɛʊ',
        'eu': u'eʊ',
        'ie2': u'iə\u0306',
        'iu': u'iʊ',
        # not sure about this one: not documented in GP handout and
        # not documented on wikipedia either...
        'oa': u'oa',
        # reversed the proposed translation which seemed really weird
        'oe': u'ʊə',
        # here and was not documented in wikipedia + shouldn't ə be
        # replaced by ɤ?
        'oi': u'ɔi',
        'oi2': u'oi',
        # shouldn't ə be replaced by ɤ?
        'oi3': u'əi',
        'ua': u'uə\u0306',
        'ua2': u'ɨə\u0306',
        'ui': u'ui',
        'ui2': u'ɨi',
        'uu2': u'ɨʊ',
        # this one is not clear
        'uy': u'uːi',
        'ieu': u'iə\u0306ʊ',
        'uoi2': u'uə\u0306i',
        'uoi3': u'ɨə\u0306i',
        'uou': u'ɨə\u0306ʊ'
    }

    consonants = {
        'b': u'ɓ',
        'ch': u'tɕ', # possibly not affricate?
        'd1': u'ɟ',
        # this phoneme is not reported in wikipedia vietnamese
        # phonology although it is said to occur in north-central
        # vietnamese dialect on wikipedia 'ɟ' page
        'd2': u'ɗ',
        'g': u'ɣ',
        'h': u'h',
        'j': u'j',
        'k': u'k',
        'kh': u'x',
        'l': u'l',
        'm': u'm',
        'n': u'n',
        'ng': u'ŋ',
        'nh': u'ɲ',
        'p': u'p',
        'ph': u'f',
        'r': u'ʐ',
        's': u'ʂ',
        't': u't',
        'th': u'tʰ',
        # possibly affricate?
        'tr': u'ʈ',
        'x': u's',
        'v': u'v'
    }

    # https://en.wikipedia.org/wiki/Vietnamese_phonology#Six-tone_analysis
    # (northern part)
    tones = [
        ('_1', u'˧'), # mid-level (neutral)
        ('_2', u'˨˩'),
        ('_3', u'˧˥'),
        ('_4', u'˧˩˧'),
        # apparently no ipa symbol for 'ˀ' (glottalized), so use
        # u'˧\u0330˥\u0330' instead of u'˧ˀ˥' (using the creaky voice
        # diacritic)
        ('_5', u'˧\u0330˥\u0330'), # + creaky voice
        # apparently no ipa symbol for 'ˀ' (glottalized), so used
        # u'˨\u0330˩\u0330ʔ' instead of u'˨ˀ˩ʔ' (using the creaky
        # voice diacritic)
        ('_6', u'˨\u0330˩\u0330ʔ') # + creaky voice
    ]

    # generate dict associating phones with ipa and tonal variants
    variants = []
    phones = consonants
    for vowel, ipa in vowels.iteritems():
        for tone, ipa_t in tones:
            tonal = vowel + tone
            assert tonal not in phones
            phones[tonal] = ipa + ipa_t

        variants.append([vowel + tone for tone, _ in tones])

    def correct_dictionary(self):
        """Correct problems with the GlobalPhone Mandarin dictionary

        The corrections are completely ad hoc the result is stored in
        a temporary file

        """
        self.log.info('Correcting dictionary')

        # the following words are in the dictionary but are not used
        # in the transcriptions they will be dropped
        words_to_drop = [u'$', u'(', u')']

        # read input file
        with utils.open_utf8(self.dictionary, 'r') as inp:
            lines = inp.readlines()

        # generate output file
        fid, corrected_dictionary = tempfile.mkstemp()
        os.close(fid)

        # correct content
        with utils.open_utf8(corrected_dictionary, 'w') as out:
            for line in lines:  #open_utf8(self.dictionary, 'r').readlines():
                # skip secondary pronunciations
                if u'(2)' not in line:
                    # skip some words
                    if all([(u'{'+word+u'}' not in line)
                            for word in words_to_drop]):
                        # rewrite tone markers in a manner consistent with
                        # GlobalPhone Mandarin pinyin markings
                        line = line.replace(u'WB ', u'WB')
                        line = line.replace(u'  ', u' ')
                        # ttd and t.t.d have wrongly formatted
                        # transcriptions
                        line = line.replace(u'{{t}', u'{t')

                        line = re.sub(ur'\{(\w*) T(\d)\}', u'\\1_\\2', line)
                        line = re.sub(ur'\{(\w*) T(\d) WB\}',
                                      u'{\\1_\\2 WB}', line)
                        out.write(line)

        self.log.info('Dictionary corrected, writed in {}'
                      .format(corrected_dictionary))
        self.dictionary = corrected_dictionary
        return True


    def correct_transcription(self):
        """Correct problems with the GlobalPhone Vietnamese transcripts

        The corrections are completely ad hoc and the result are
        stored in a temporary folder.

        - remove trailings spaces and all double spacings and '_' from
          transcriptions on every odd line but the first

        - double spacings and '_' are actually only found for speakers
          200 to 208

        """
        # generate temporary output folder
        corrected_transcription_dir = tempfile.mkdtemp()

        # get the list of transcription files
        trss = utils.list_directory(self.transcription_dir, abspath=True)

        self.log.info('correcting {} transcription files in {}'
                      .format(len(trss), corrected_transcription_dir))

        for trs in trss:
            # read transcript file
            lines = utils.open_utf8(trs, 'r').readlines()

            # correct odd lines
            lines[2::2] = [line.replace(u'_', u' ').replace(u'  ', u' ').strip()
                           + u'\n' for line in lines[2::2]]

            # write corrected version to temp
            output_file = os.path.join(corrected_transcription_dir, trs)
            with utils.open_utf8(output_file, 'w') as out:
                for line in lines:
                    out.write(line)

        self.log.info('Transcripts corrected, writed to {}'.
                      format(self.transcription_dir))
        self.transcription_dir = corrected_transcription_dir
        return True
