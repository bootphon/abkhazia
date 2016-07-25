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
"""Data preparation for Childes data

This script has designed to process data in English but could be
adapted for other languages.

We used the Brent corpus as a test case because we had the wav files
for this corpus (not all corpora in CHILDES are provided with audio
files. We exclude c1, v1 and v2 subjects because the recordings were
of bad quality. Structure of each corpus is the following: 1 folder
for each subject with all its corresponding files (cha, wav...)

"""

import collections
import os
import re

import phonemizer
import abkhazia.utils as utils
from abkhazia.corpus.prepare import AbstractPreparator


# TODO extend this preparator to other copora than Brent. The corpora
# with associated audio are in http://childes.psy.cmu.edu/media/
class ChildesPreparator(AbstractPreparator):
    """Convert Childes data (in cha format) into the abkhazia format"""

    name = 'childes'
    description = 'Child Language Data Exchange System'

    long_description = '''
    The Child Language Data Exchange System (CHILDES) is a corpus
    established in 1984 by Brian MacWhinney and Catherine Snow to
    serve as a central repository for first language acquisition
    data. Its earliest transcripts date from the 1960s, and it now has
    contents (transcripts, audio, and video) in 26 languages from 130
    different corpora, all of which are publicly available worldwide.
    Recently, CHILDES has been made into a component of the larger
    corpus TalkBank, which also includes language data from aphasics,
    second language acquisition, conversation analysis, and classroom
    language learning.  CHILDES is mainly used for analyzing the
    language of young children and the child directed speech of
    adults.  The transcriptions are coded in the CHAT (Codes for the
    Human Analysis of Transcripts) transcription format, which
    provides a standardized format for producing conversational
    transcripts.  CHILDES is currently directed and maintained by
    Brian MacWhinney at Carnegie Mellon University.'''

    url = 'http://childes.psy.cmu.edu/'
    audio_format = 'wav'

    # IPA transcriptions for all phones in the Childes corpus.
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
        'ax': u'ə',
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
        'l': u'l',
        'r': u'r',
        'w': u'w',
        'y': u'j',
        'hh': u'h',
    }

    silences = [u"SIL_WW", u"NSN"]  # SPN and SIL will be added automatically

    variants = []  # could use lexical stress variants...

    # Modify this to select the lines you want, for example here, we
    # exclude speech by children and non-humans. List of specific
    # names we needed to add to eliminate speech from target child and
    # non-adults:
    #
    # Bloom70/Peter/*.cha   JEN     Child
    # Bloom70/Peter/*.cha   JEN     Sister
    # Brent/w1-1005.cha     MAG     Target_Child
    # Brown/Adam/*.cha      CEC     Cousin
    # Brown/Adam/adam23.cha PAU     Brother
    # Brown/Sarah/sarah019.cha      ANN     Cousin
    # Brown/Sarah/sarah020.cha      JOA     Child
    # Brown/Sarah/sarah046.cha      SAN     Playmate
    # Clark/shem15.cha      BRU     Child
    # Clark/shem15.cha      CAR     Child
    # Clark/shem15.cha      LEN     Child
    # Clark/shem37.cha      JEM     Child
    # Cornell/moore189.cha  JOS     Child
    # Feldman/09.cha        STV     Target_Child
    # Feldman/*.cha LAR     Child
    # MacWhinney/08a.cha    MAD     Child
    # MacWhinney/*.cha      MAR     Brother
    # Sachs/n61na.cha       JEN     Playmate
    # Weist/Roman/rom*.cha  SOP     Sister
    exclude = ('SI.|BR.|CHI|TO.|ENV|BOY|NON|MAG|JEN|MAG|CEC|PAU|'
               'ANN|JOA|SAN|BRU|CAR|LEN|JEM|JOS|STV|LAR|MAD|MAR|SOP')

    def __init__(self, input_dir,  log=utils.logger.null_logger(), copy_wavs=False):
        """Childes preparator initialization

        If `copy_wavs` is True, copy the wavs file to `output_dir`,
        else symlinks them.

        Select the cha files with only one adult speaking.

        """
        # call the AbstractPreparator __init__
        super(ChildesPreparator, self).__init__(input_dir, log=log)
        self.copy_wavs = copy_wavs
        self.chas = self._select_chas(one_adult=True)
        self.utts = self._parse_chas(self.chas, self.exclude)

    def _select_chas(self, one_adult=True):
        """Return a dict of (cha files: attached wav) entries

        If `one_adult` is True, select the cha files with only one
        adult speaking, else select all the transcriptions. The
        returned paths are relative to self.input_dir.

        """
        chas = utils.list_files_with_extension(self.input_dir, '.cha')
        if one_adult:
            chas = [c for c in chas if utils.cha.nadults(c) == 1]
        self.log.debug(
            'found %s cha files%s', len(chas),
            ' with only one adult speaker' if one_adult else '')

        # a dict mapping wavs basename (as they are refered to in cha
        # files) to their full path
        wavs_dict = dict(
            (os.path.splitext(os.path.basename(w))[0], w)
            for w in utils.list_files_with_extension(self.input_dir, '.wav'))

        cha_dict = dict()
        for cha in chas:
            try:
                wav = utils.cha.audio(cha)
                cha_dict[cha] = wavs_dict[wav]
            except IOError:
                self.log.debug(
                    'ignoring cha with no attached wav: %s', cha)
            except KeyError:
                self.log.debug(
                    'ignoring cha because attached wav not found: %s', cha)

        self.log.debug(
            'using %s cha files and %s wav files',
            len(cha_dict), len(set(cha_dict.values())))

        return cha_dict

    Utterance = collections.namedtuple(
        'Utterance', 'text wav tbegin tend')
    """Namedtuple storing an utterance parser from a cha file"""

    def _parse_chas(self, chas, exclude_spks):
        """Extract cleaned utterances from raw cha files

        Return a dict of utterances where keys are the utterances id and
        values are Utterance named tuples.

        a) the ones considered will be only the ones marked with time-stamps
        b) whose timestamps correspond to wav duration
        c) utterances that are not empty

        """
        self.log.info('parsing %s cha files...', len(chas))
        utts = {}
        for cha, wav in chas.iteritems():
            # duration of the wav in millisecond
            duration = utils.wav.duration(wav)

            # get cleaned utterances from the raw cha file. At that
            # point timestamps are the last word of each line.
            text = utils.cha.clean(
                l.strip() for l in utils.open_utf8(cha, 'r')
                if not re.search(exclude_spks, l))

            cha_id = os.path.splitext(os.path.basename(cha))[0]
            counter = 0
            for words in (t.split() for t in text):
                if len(words) > 1:  # remove empty utterances
                    # parsing the timestamps
                    timestamp = words[-1].split('_')
                    tbegin = int(timestamp[0])/1000.
                    tend = int(timestamp[1])/1000.

                    # reject utterances with out of boundaries
                    # timestamps
                    if not (tbegin > duration or tend > duration):
                        counter += 1
                        utt_id = cha_id + '-sent' + str(counter)

                        utts[utt_id] = self.Utterance(
                            ' '.join(words[:-1]),
                            os.path.basename(wav),
                            tbegin, tend)

        return utts

    def list_audio_files(self):
        return [w for w in self.chas.itervalues()]

    def make_segment(self):
        segments = dict()
        for k, v in self.utts.iteritems():
            segments[k] = (os.path.splitext(os.path.basename(v.wav))[0],
                           float(v.tbegin), float(v.tend))
        return segments

    def make_speaker(self):
        utt2spk = dict()
        for key in self.utts.iterkeys():
            utt2spk[key] = re.sub('-(.*)-(.*)', '', key)
        return utt2spk

    def make_transcription(self):
        text = dict()
        for k, v in self.utts.iteritems():
            # separate collocations into words for the phonemizer:
            # thank_you", delete the letter tag of childes: a@l
            # means letter a
            text[k] = re.sub('@[a-z]', '', v.text.replace('_', ' '))
        return text

    def make_lexicon(self):
        # retrieve all words in transcriptions. Separate collocations
        # into words for phonologizer, e.g. thank_you -> thank you,
        # delete the letter tag of childes: a@l means letter a, split
        # the utterances words.
        words = sorted(set(
            word for utt in self.utts.itervalues() for word in
            re.sub('@[a-z]', '', utt.text.replace('_', ' ')).split(' ')
            if word != ''))

        # initializing the phonemizer
        p = phonemizer.Phonemizer(logger=self.log)
        p.separator = phonemizer.Separator('', '', ' ')
        p.strip_separator = False

        # phonemize the words
        self.log.info('phonemizing %s words', len(words))
        return dict(zip(
            words, (w.strip() for w in p.phonemize(words, njobs=self.njobs))))
