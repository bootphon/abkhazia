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
"""Data preparation for the revised Buckeye corpus"""

import collections
import joblib
import os
import re

import abkhazia.utils as utils
from abkhazia.corpus.prepare import AbstractPreparator


def _split_raw_utt(raw_utt):
    split_re = ('<CUTOFF-.+?>|<EXCLUDE-.+?>|<HES-.+?>|<Hes-.+?>|'
                '<EXT-.+?>|<EXt-.+?>|<EXT_.+?>|<LAUGH-.+?>|<LAUGH>|<ERROR.*?>')
    return [u.strip() for u in re.split(split_re, raw_utt)]

_Word = collections.namedtuple('Word', 'word, time')


def _load_word(line):
    """Return a pair (word/time) for a line from a *.words_fold file"""
    match = re.match(
        r'\s*(.*)\s+(121|122)\s(.*);(.*); (.*); (.*)', line)
    assert match, line

    return _Word(word=match.group(3), time=float(match.group(1)))


def _parse_utterances(txt_file, phn_file, log):
    segments = dict()
    utt2spk = dict()
    text = dict()

    # log.info('loading %s', os.path.basename(txt_file))

    # /path/to/.../s2202b.txt -> s2202b
    speaker_id = os.path.splitext(os.path.basename(txt_file))[0]

    # load the current files
    txt_data = [l.strip() for l in open(txt_file, 'r') if l.strip()]
    phn_data = [_load_word(l)
                for l in open(phn_file, 'r').readlines()[9:]
                if l.strip()]

    # check we have the same number of words in txt and phn
    if len(phn_data) != sum(len(l.split()) for l in txt_data if l):
        raise AssertionError(
            '{} and {} have a different word count, exiting'
            .format(txt_file, phn_file))

    # split raw utterances (lines) into cleaned subutterances
    utterances = [
        l for l in
        sum([_split_raw_utt(line) for line in txt_data], []) if l]
    phn_index = 0
    for utt_index, utt_txt in enumerate(utterances, start=1):
        utt_id = '{}-sent{}'.format(speaker_id, utt_index)
        utt_words = utt_txt.split()

        while utt_words[0] != phn_data[phn_index].word:
            # self.log.warning('skipping %s', phn_data[phn_index].word)
            phn_index += 1

        tstart = phn_data[phn_index-1].time if phn_index else 0
        phn_index += len(utt_words) - 1
        assert phn_data[phn_index].word == utt_words[-1], \
            'match error: {}\t{}'.format(
                phn_data[phn_index].word, utt_words[-1])

        tstop = phn_data[phn_index].time
        phn_index += 1

        segments[utt_id] = (speaker_id, tstart, tstop)
        utt2spk[utt_id] = speaker_id
        text[utt_id] = re.sub('{(B|E)_TRANS}', '', utt_txt)

    return (segments, utt2spk, text)


class BuckeyePreparator(AbstractPreparator):
    """Convert the Buckeye corpus to the abkhazia format"""

    name = 'buckeye'
    url = 'http://buckeyecorpus.osu.edu'
    audio_format = 'wav'
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

    # IPA transcriptions for all phones in the Buckeye corpus. The
    # following phones are never found in the transcriptions: set([u'own',
    # u'ahn', u'ihn', u'ayn', u'NSN', u'eyn', u'oyn', u'ehn', u'iyn',
    # u'B', u'E', u'uhn', u'aon', u'awn', u'uwn', u'aan', u'ern', u'aen'])
    # Reason: we already collapsed them in the foldings_version

    # 20th March 2017 update :
    # Some tags are removed or mapped differently to keep
    # a coherence between different corpora. :
    # - {B_TRANS} and {E_TRANS} are removed sinc they only mark the
    # begining and end of the transcription
    # - VOCNOISE and LAUGH are mapped to SPN (spoken noise)
    # - NOISE and IVER are mapped to NSN (non spoken noise)
    #
    # June 2017 update :
    # - The following folds are folded: em -> m, en -> n, eng -> ng
    #   and el -> l
    phones = {
        'aa': u'ɑː',
        'ae': u'æ',
        'ah': u'ʌ',
        'ao': u'ɔː',
        'aw': u'aʊ',
        'ay': u'aɪ',
        'eh': u'ɛ',
        'er': u'ɝ',
        'ey': u'eɪ',
        'iy': u'iː',
        'ih': u'ɪ',
        'oy': u'ɔɪ',
        'ow': u'oʊ',
        'uh': u'ʊ',
        'uw': u'uː',
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
        'l': u'l',
        'r': u'r',
        'w': u'w',
        'y': u'j',
        'hh': u'h',
        'tq': u'ʔ',
        'CUTOFF': u'CUTOFF',
        'ERROR': u'ERROR',
        'EXCLUDE': u'EXCLUDE',
        'UNKNOWN_WW': u'UNKNOWN_WW',
        'UNKNOWN': u'UNKNOWN',
        'HESITATION_TAG': u'HESITATION_TAG',
        'LENGTH_TAG': u'LENGTH_TAG',
    }

    silences = [u"NSN"]  # SPN and SIL will be added automatically

    variants = []  # could use lexical stress variants...

    def __init__(self, input_dir, log=utils.logger.null_logger(),
                 copy_wavs=False, njobs=4):
        super(BuckeyePreparator, self).__init__(input_dir, log=log)
        self.copy_wavs = copy_wavs

        self.segments = dict()
        self.text = dict()
        self.utt2spk = dict()

        # the input text and lexicon files we will parse
        txt_files = self._list_files('.txt', exclude=['readme'])
        phn_files = [f.replace('.txt', '.words_fold') for f in txt_files]

        # for each pair of text/lexicon files, update the
        # segments/text/utt2spk dictionaries
        res = joblib.Parallel(
            n_jobs=njobs, verbose=0, backend="threading")(
                joblib.delayed(_parse_utterances)
                (txt_file, phn_file, self.log)
                for txt_file, phn_file in zip(txt_files, phn_files))

        for s, u, t in res:
            self.segments.update(s)
            self.utt2spk.update(u)
            self.text.update(t)

    def _list_files(self, ext, exclude=None, abspath=False, realpath=False):
        files = utils.list_files_with_extension(
            self.input_dir, ext, abspath=abspath, realpath=realpath)

        if exclude is not None:
            files = [f for f in files for e in exclude if e not in f]

        return files

    def list_audio_files(self):
        return self._list_files('.wav', abspath=True, realpath=True)

    def make_segment(self):
        return self.segments

    def make_speaker(self):
        return self.utt2spk

    def make_transcription(self):
        t = self.text
        t['s2202b-sent29'] = t['s2202b-sent29'].replace("p's", "p")
        return t

    def make_lexicon(self):
        """Build the buckeye lexicon from the *.words_fold files"""
        lexicon = dict()
        no_lexicon = set()

        files = self._list_files('.words_fold')
        for line in (l for f in files for l in open(f, 'r')):
            match = re.match(
                r'\s\s+(.*)\s+(121|122)\s(.*);(.*); (.*); (.*)', line)

            if match:
                word = match.group(3)
                phones = match.group(5)

                # merge phones together
                phones = phones.replace('em', 'm')
                phones = phones.replace('el', 'l')
                phones = phones.replace('en', 'n')
                phones = phones.replace('eng', 'ng')
                phones = phones.replace('nx', 'dx')

                # replace VOCNOISE/VOCNOISE_WW/LAUGH by SPN
                phones = phones.replace('UNKNOWN_WW', 'SPN')
                phones = phones.replace('UNKNOWN', 'SPN')
                phones = phones.replace('VOCNOISE_WW', 'SPN')
                phones = phones.replace('VOCNOISE', 'SPN')
                phones = phones.replace('LAUGH', 'SPN')

                # replace IVER/NOISE/NOISE_WW by NSN
                phones = phones.replace('NOISE_WW', 'NSN')
                phones = phones.replace('NOISE', 'NSN')
                phones = phones.replace('IVER', 'NSN')

                # add the word to lexicon
                if phones:
                    # TODO Here we can check if (and when) we have
                    # several transcriptions per word (alternate
                    # pronunciations) and choose the most FREQUENT
                    # one. Here we are keeping only the most RECENT.
                    lexicon[word] = phones
                else:
                    no_lexicon.add(word)

        # detect the words with no transcription
        really_no_lexicon = [t for t in no_lexicon if t not in lexicon]
        if really_no_lexicon:
            self.log.debug(
                'following words have no transcription in lexicon: {}'
                .format(really_no_lexicon))

        # retain only the words present in the text
        corpus_words = set(w for u in self.text.values() for w in u.split())
        return {k: v for k, v in lexicon.items() if k in corpus_words}


# TODO The following code is dedicated to manual alignments. It should
# be more integrated with abkhazia (mayebe have a
# BuckeyeAlignedPreparator child class?). See also
# abkhazia/egs/triphones_buckeye.py for an exemple of how to use the
# GetAlignment class
#
# For now the preparator works on word alignments to extract segments
# (utterances boundaries). But there is a lot of little differences in
# words/phones levels alignments in Buckeye, about 1/3 of utterances
# are concerned.

class GetAlignment:
    """Extract Buckeye manual phone alignments at utterance level"""
    def __init__(self, buckeye_dir):
        self.alignment = {}
        self.buckeye_dir = buckeye_dir

    def __call__(self, record, tstart, tstop):
        """Return phones alignment for a given record interval"""
        if record not in self.alignment:
            self._load_record(record)

        return list(self._yield_utt(record, tstart, tstop))

    def _load_record(self, record):
        """Init self.alignment with a given record, load the file"""
        record_file = os.path.join(
            self.buckeye_dir, record[:3], record, record + '.phones_fold')

        self.alignment[record] = [a for a in self._yield_file(record_file)]

    def _yield_file(self, record_file):
        """Yield (tstart, tstop, phone) from a phones alignment file"""
        tstart = 0.0
        for line in (
                l[2:] for l in open(record_file, 'r') if l.startswith('  ')):
            tstop, _, phone = line.split()
            yield float(tstart), float(tstop), phone
            tstart = tstop

    def _yield_utt(self, record, tstart, tstop):
        """Yield (tstart, tstop, phone) for a given record interval"""
        for begin, end, phone in self.alignment[record]:
            if end >= tstop:
                yield begin, end, phone
                break
            if begin >= tstart:
                yield begin, end, phone


def validate_phone_alignment(corpus, alignment, log=utils.logger.get_log()):
    """Return True if the phone alignment is coherent with the corpus

    Return False on any other case, send a log message for all
    suspicious alignments.

    """
    error_utts = set()
    # check all utterances one by one
    for utt in corpus.utts():
        # corpus side
        _, utt_tstart, utt_tstop = corpus.segments[utt]

        # alignment side
        ali_tstart = alignment[utt][0][0]
        ali_tstop = alignment[utt][-1][1]

        # validation
        if utt_tstart != ali_tstart:
            error_utts.add(utt)
            log.warn(
                '%s tstart error in corpus and alignment (%s != %s)',
                utt, utt_tstart, ali_tstart)

        if utt_tstop != ali_tstop:
            error_utts.add(utt)
            log.warn(
                '%s : tstop error in corpus and alignment: %s != %s',
                utt, utt_tstop, ali_tstop)

    if error_utts:
        log.error(
            'timestamps are not valid for %s/%s utterances',
            len(error_utts), len(corpus.utts()))
        return False

    log.info('alignment is valid for all utterances')
    return True
