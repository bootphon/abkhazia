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

from collections import defaultdict
import contextlib
import os
import pkg_resources
import re
import tempfile
import wave

import phonemizer

import abkhazia.utils as utils
from abkhazia.utils import list_files_with_extension
from abkhazia.prepare import AbstractPreparator


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

    def __init__(self, input_dir, output_dir=None,
                 verbose=False, njobs=1, copy_wavs=False):
        # call the AbstractPreparator __init__
        super(ChildesPreparator, self).__init__(
            input_dir, output_dir, verbose, njobs)

        self.copy_wavs = copy_wavs
        # self.tmpdir = os.path.join(self.output_dir, 'tmp')
        self.tmpdir = tempfile.mkdtemp()
        self._clean_tmpdir = True

        # write cleaned utterances to self.tmpdir
        self._extract_cds()
        self.cha2wav = self._match_cha_with_wav()
        self.dict_utts = self._select_utts_with_timestamps()

    def __del__(self):
        if self._clean_tmpdir:
            utils.remove(self.tmpdir, safe=True)

    def _extract_cds(self):
        """Extract child directed utterances

        For each subject, extract only the utterances produced by adults to
        the child and generate 2 files: (For that reason, the output may not
        necessarily have the same number as the cha files)

        - includedlines: utterances by mother + time stamps if any + first
        line is the name of the corresponding wav
        - ortholines: utterances cleaned

        This function calls a bash script that was developed for Alex
        Cristia's segmentation project. The script was slightly modified
        to fit our purposes. It was extensively commented so you can have
        more details there.

        """
        self.log.info('extracting child directed speech to %s', self.tmpdir)

        script = pkg_resources.resource_filename(
            pkg_resources.Requirement.parse('abkhazia'),
            'abkhazia/share/childes_cleanup.sh')

        utils.jobs.run(
            ' '.join([script, self.input_dir, self.tmpdir,
                      os.path.dirname(script)]),
            stdout=self.log.debug)

    def _select_utts_with_timestamps(self):
        """Select the utterances used for the alignment

        a) the ones considered will be only the ones marked with time-stamps
        b) whose timestamps correspond to wav duration
        c) utterances that are not empty

        """
        # mapping from each wav file to its duration
        dict_wav = {}
        for wav in list_files_with_extension(self.input_dir, '.wav'):
            with contextlib.closing(wave.open(wav, 'r')) as f:
                duration = f.getnframes() / float(f.getframerate())
            basewav = os.path.splitext(os.path.basename(wav))[0]
            dict_wav[basewav] = duration

        # create a dict of utterances where keys are the sentence id and
        # values are lists of : 1) the sentence and 2) the timestamp
        dict_utts = defaultdict(list)
        cds_dir = os.path.join(self.tmpdir, 'cds_files')
        for ortho in list_files_with_extension(cds_dir, '-ortholines.txt'):
            base_ortho = os.path.splitext(os.path.basename(ortho))[0]
            speaker_id = base_ortho.replace('-ortholines', '')

            wav_id = open(ortho.replace('ortho', 'included'))\
                .readline()\
                .replace('@Media:', '')\
                .replace(', audio', '')\
                .strip()

            index_sent = 0
            rejected = 0
            for line in utils.open_utf8(ortho, 'r'):
                # looking for timestamps for each utterance
                words = line.split()
                if not re.match("([0-9]+)_([0-9]+)", words[-1]):
                    rejected += 1
                else:  # timestamps found for that utterance
                    index_sent += 1
                    utt_id = speaker_id + '-sent' + str(index_sent)
                    sent = " ".join(words[:-1])
                    timestamp = words[-1]

                    # reject empty lines even if we have timestamps
                    if sent == "":
                        rejected += 1
                    else:  # if offset > wav duration, sentence is rejected
                        offset_sec = float(timestamp.split('_')[1])/1000
                        duration = dict_wav[wav_id]
                        if offset_sec > duration:
                            rejected += 1
                        else:  # if time is ok, sentence will be considered
                            dict_utts[utt_id].append(sent)
                            dict_utts[utt_id].append(timestamp)
            if rejected != 0:
                self.log.debug(
                    'rejected %s utterances from %s', rejected, speaker_id)

        return dict_utts

    def _match_cha_with_wav(self):
        """This function finds the matching wavs for transcripts we ended up
        using after the first clean-up step (see above)

        """
        wavs = [os.path.basename(w).replace('.wav', '')
                for w in list_files_with_extension(
                        self.input_dir, '.wav', abspath=False)]

        # Mapping cha file -> wav file
        dict_cha = {}
        for cha in list_files_with_extension(self.input_dir, '.cha'):
            for line in open(cha).readlines():
                # Extract name of media file
                m_line = re.match("^@Media:\t(.*), audio", line)
                if m_line:  # exclude cha files with no wav file attached
                    wav = m_line.group(1)
                    if wav not in wavs:
                        self.log.debug('cha file not matched: ' + cha)
                    else:
                        dict_cha[cha] = os.path.join(os.path.dirname(cha), wav)

        return dict_cha

    def list_audio_files(self):
        wavs = [w + '.wav' for w in self.cha2wav.itervalues()]
        return wavs, [os.path.basename(w) for w in wavs]

    def make_segment(self):
        # mapping from utterance id to wav file
        cha2wav = dict(
            (os.path.splitext(os.path.basename(k))[0], os.path.basename(v))
            for k, v in self.cha2wav.iteritems())
        utt2wav = {}
        for u in self.dict_utts.iterkeys():
            uttid = '-'.join(os.path.basename(u).split('-')[:-1])
            utt2wav[uttid] = cha2wav[uttid]

        with open(self.segments_file, 'w') as outfile:
            for key, value in sorted(self.dict_utts.items()):
                wav = utt2wav['-'.join(os.path.basename(key).split('-')[:-1])]
                time = value[1].split('_')
                onset = float(time[0])/1000
                offset = float(time[1])/1000
                outfile.write(' '.join(
                    [key, wav + '.wav', str(onset), str(offset)]) + '\n')

    def make_speaker(self):
        with open(self.speaker_file, 'w') as outfile:
            for k in sorted(self.dict_utts):
                speaker_id = re.sub('-(.*)-(.*)', '', k)
                outfile.write(k + ' ' + speaker_id + '\n')

    def make_transcription(self):
        with open(self.transcription_file, "w") as outfile:
            for k, values in sorted(self.dict_utts.items()):
                sent = values[0]
                # separate collocations into words for phonologizer: thank_you"
                sent = sent.replace('_', ' ')
                # delete the letter tag of childes: a@l means letter a
                sent = re.sub('@[a-z]', '', sent)
                outfile.write(k + ' ' + sent + '\n')

    def make_lexicon(self):
        # retrieve all words in transcriptions
        words = set()
        for value in self.dict_utts.itervalues():
            sent = value[0]
            # separate collocations into words for phonologizer,
            # e.g. thank_you
            sent = sent.replace('_', ' ')
            # delete the letter tag of childes: a@l means letter a
            sent = re.sub('@[a-z]', '', sent)

            # split the utterances words
            for w in sent.split(' '):
                if w.strip() != '':
                    words.add(w)
        words = sorted(words)

        # initializing the phonemizer
        p = phonemizer.Phonemizer(logger=self.log)
        p.separator = phonemizer.Separator('', '', ' ')
        p.strip_separator = False

        # phonemize the words
        self.log.info('phonemizing %s words', len(words))
        lexicon = dict(zip(
            words, (w.strip() for w in p.phonemize(words, njobs=self.njobs))))

        # finally write the lexicon file from the lexicon dict
        with open(self.lexicon_file, 'w') as outfile:
            for key, value in lexicon.iteritems():
                outfile.write(key + ' ' + value.strip() + '\n')
