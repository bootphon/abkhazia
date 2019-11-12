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
"""Provides the Corpus class"""

import os

from abkhazia.corpus.corpus_saver import CorpusSaver
from abkhazia.corpus.corpus_loader import CorpusLoader
from abkhazia.corpus.corpus_validation import CorpusValidation
from abkhazia.corpus.corpus_split import CorpusSplit
from abkhazia.corpus.corpus_merge_wavs import CorpusMergeWavs
from abkhazia.corpus.corpus_filter import CorpusFilter
from abkhazia.corpus.corpus_trimmer import CorpusTrimmer
import abkhazia.utils as utils


class Corpus(utils.abkhazia_base.AbkhaziaBase):
    """Speech corpus in the abkhazia format

    This class wraps a speech corpus in the abkhazia format and
    provides methods/attritutes to interact with it in a consistent
    and safe way.

    Attributes
    ==========

    wav_folder: str
    ---------------

    - folder where wav files associated to the corpus are stored

    wavs: set(wav_id)
    ------------------------

    - basename of the corpus wav files
    - exemple: ('s01.wav')

    lexicon: dict(word, phones)
    ---------------------------

    - dictionary of corpus words to phones
    - word and phones are both str, phones are separated by ' '
    - exemple: ('weeks', 'w iy k s')

    segments: dict(utt_id, (wav_id, tbegin, tend))
    ----------------------------------------------

    - time interval in wav files mapped to each corpus utterance
    - tbegin and tend are None if the wav file contains a single
      utterance, else they correspond to begin and end times in the
      wav (in seconds, as float)
    - exemple: ('s01u01', ('s01.wav', 0, 0.75))

    text: dict(utt_id, str)
    -----------------------

    - transcription associated to each corpus utterance
    - exemple: ('s01u01', 'yeah <SIL> oh yeah')

    utt2spk: dict(utt_id, spk_id)
    -----------------------------

    - corpus utterances mapped to their speaker
    - exemple: ('s01u01', 's01')

    phones: dict(str, str)
    ----------------------

    - corpus phones mapped to their IPA equivalent
    - exemple: ('iy', u'iː')

    silences: list(str)
    -------------------

    - corpus silence phones
    - exemple: ['<SIL>']

    variants: list(str)
    -------------------

    TODO implement variants phones
    - alternative phones variants (not yet implemented)
    - exemple: []

    """

    @classmethod
    def load(cls, corpus_dir, validate=False, log=utils.logger.null_logger()):
        """Return a corpus initialized from `corpus_dir`

        If validate is True, make sure the corpus is valid before
        returning it.

        Raise IOError if corpus_dir if an invalid directory, the
        output corpus is not validated.

        """
        return CorpusLoader.load(cls, corpus_dir, validate=validate, log=log)

    def __init__(self, log=utils.logger.null_logger()):
        """Initialize an empty corpus"""
        super(Corpus, self).__init__(log=log)

        self.wav_folder = ''
        self.wavs = set()
        self.lexicon = dict()
        self.segments = dict()
        self.text = dict()
        self.phones = dict()
        self.utt2spk = dict()
        self.silences = []
        self.variants = []

    def save(self, path, no_wavs=False, copy_wavs=True, force=False):
        """Save the corpus to the directory `path`

        :param str path: The output directory is assumed to be a non
            existing directory (or use force=True to overwrite it).

        :param bool no_wavs: when True, dont save the wavs (ie don't
            write wavs subdir in `path`)

        :param bool copy_wavs: when True, make a copy of the wavs
            instead of symbolic links

        :param bool force: when True, overwrite `path` if it is
            already existing

        :raise: OSError if force=False and `path` already exists

        """
        self.log.info('saving corpus to %s', path)

        if force and os.path.exists(path):
            self.log.warning('overwriting existing path: %s', path)
            utils.remove(path)

        CorpusSaver.save(self, path, no_wavs=no_wavs, copy_wavs=copy_wavs)

    def validate(self, njobs=utils.default_njobs()):
        """Validate speech corpus data

        Raise IOError on the first encoutered error, relies on the
        CorpusValidation class.

        """
        CorpusValidation(self, njobs=njobs, log=self.log).validate()

    def is_valid(self, njobs=utils.default_njobs()):
        """Return True if the corpus is in a valid state"""
        try:
            self.validate(njobs=njobs)
        except IOError:
            return False
        return True

    def utts(self):
        """Return the list of utterance ids stored in the corpus"""
        return list(self.utt2spk.keys())

    def spks(self):
        """Return the list of speaker ids stored in the corpus"""
        return list(self.spk2utt().keys())

    def spk2utt(self):
        """Return a dict of speakers mapped to an utterances list

        Built from self.utt2spk. This method is a Python
        implementation of the Kaldi script
        egs/wsj/s5/utils/utt2spk_to_spk2utt.pl.

        """
        # init an empty list for all speakers
        spk2utt = {spk: [] for spk in set(self.utt2spk.values())}

        # populate lists with utterance ids
        for utt, spk in self.utt2spk.items():
            spk2utt[spk].append(utt)
        return spk2utt

    def wav2utt(self):
        """Return a dict of wav-ids mapped to utterances/timestamps they contain

        The values of the returned dict are tuples (utt-id, tstart,
        tend). Built on self.segments.

        """
        # init an empty list for all wavs
        wav2utt = {wav: [] for wav, _, _ in self.segments.values()}

        def _float(t):
            return None if t is None else float(t)

        # populate lists with utterance ids and timestamps
        for utt, (wav, tstart, tend) in self.segments.items():
            wav2utt[wav].append((utt, _float(tstart), _float(tend)))
        return wav2utt

    def utt2duration(self):
        """Return a dict of utterances ids mapped to their duration

        Durations are floats expressed in second, read from wav files

        """
        utt2dur = dict()
        for utt, (wav, start, stop) in self.segments.items():
            start = 0 if start is None else start
            wav_path = os.path.join(self.wav_folder, wav)
            stop = utils.wav.duration(wav_path) if stop is None else stop
            utt2dur[utt] = stop - start
        return utt2dur

    def duration(self, format='seconds'):
        """Return the total duration of the corpus

        If `format` is 'second', returns the corpus duration in
        seconds as a float. If `format` is 'datetime', returns the
        corpus duration as a string in the 'hh:mm:ss' format.

        Raise IOError if `format` is not 'seconds' or 'datetime'

        """
        total = sum(self.utt2duration().values())
        if format == 'seconds':
            return total
        elif format == 'datetime':
            import datetime
            # format as hh:mm:ss, skipping subseconds
            return str(datetime.timedelta(seconds=total)).split('.')[0]
        else:
            raise IOError('Unknow format for corpus duration (%s)', format)

    def words(self, in_lexicon=True):
        """Return a set of words composing the corpus

        The listed words are present in both text and lexicon (if
        `is_lexicon` is True), or in text only. The returned result is
        a set for search efficiency.

        """
        return set(
            word for utt in self.text.values() for word in utt.split()
            if (word in self.lexicon if in_lexicon else True))

    def has_several_utts_per_wav(self):
        """Return True if there is several utterances in at least one wav"""
        for _, start, stop in self.segments.values():
            if start is not None or stop is not None:
                return True
        return False

    def subcorpus(self, utt_ids, prune=True, name=None, validate=True):
        """Return a subcorpus made of utterances in `utt_ids`

        The returned corpus is validated (except if `validate` is
        False) and pruned (except if `prune` is False).

        Raise a KeyError if one utterance in `utt_ids` is in the
        input corpus.

        Raise an IOError if the subcorpus is not valid (this should
        not occurs if the input corpus is valid).

        """
        corpus = Corpus()
        corpus.meta.source = self.meta.source
        corpus.meta.name = name if name else 'subcorpus of ' + self.meta.name
        corpus.meta.comment = ('{} utterances from {}'
                               .format(len(utt_ids), len(self.utts())))

        corpus.lexicon = self.lexicon
        corpus.phones = self.phones
        corpus.silences = self.silences
        corpus.variants = self.variants

        corpus.wav_folder = self.wav_folder
        corpus.wavs = self.wavs

        corpus.segments = dict()
        corpus.text = dict()
        corpus.utt2spk = dict()
        for utt in utt_ids:
            corpus.segments[utt] = self.segments[utt]
            corpus.text[utt] = self.text[utt]
            corpus.utt2spk[utt] = self.utt2spk[utt]

        if prune:
            corpus.prune()
        if validate:
            corpus.validate()
        return corpus

    def prune(self, prune_lexicon=False):
        """Removes unregistered utterances from a corpus

        This method modifies the corpus in place and return None

        The pruning operation delete undesired data from utterances
        listed in self.utts(). It removes any segment, text, wav with
        an unknown utterance id.

        If prune_lexicon is True, it also prunes the lexicon and
        phoneset.
        """
        utts = set(self.utts())

        # prune utterance indexed dicts from the utterances list
        for d in (self.segments, self.text, self.utt2spk):
            d = {key: value for key, value in d.items()
                 if key in utts}

        # prune wavs from pruned segments
        self.wavs = {utils.append_ext(w) for w in set(self.wav2utt().keys())}

        if prune_lexicon:
            # prune lexicon from pruned text
            words = self.words(in_lexicon=False)
            self.lexicon = {key: value for key, value in self.lexicon.items()
                            if key in words}
            # make sure <unk> is still here (needed by Kaldi programs)
            self.lexicon['<unk>'] = 'SPN'

            # prune phones from pruned lexicon
            phones = set(phone for phones in self.lexicon.values()
                         for phone in phones.split())
            self.phones = {key: value for key, value in self.phones.items()
                           if key in phones}

    def remove_phones(self, phones=None, silences=None):
        """Returns a subcorpus with the specified phones/silences removed

        phones : iterable | None, list of phones to remove from corpus

        silences : iterable | None, list of silences to remove from corpus

        The phones/silences are removed from the phoneset/list of
        silences, the corpus is pruned from utterances containing any
        of these phones/silences and any dictionary entry containing
        any of the phones/silences is removed from the lexicon.

        Useful to remove infrequent phones or certain types of noise
        from a corpus.

        TODO What about variants?

        """
        if phones is None:
            phones = []
        if silences is None:
            silences = []
        for phone in phones:
            if phone not in self.phones:
                self.log.info(
                    'Phone to be removed %s not in phoneset!', phone)
        for silence in silences:
            if silence not in self.silences:
                self.log.info(
                    'Silence to be removed %s not in silences!', silence)

        all_symbols = phones + silences
        words = [word for word, w_phones in self.lexicon.items()
                 if set.intersection(set(w_phones.split(' ')), all_symbols)]
        self.log.info(
            'Removing %s lexicon words with undesirable phones/silences',
            len(words))

        utt_ids = [utt for utt, text in self.text.items()
                   if set.intersection(set(text.split(' ')), words)]
        self.log.info(
            'Removing %s utterances with undesirable phones/silences',
            len(utt_ids))
        kept_utts = [
            utt_id for utt_id in self.utt2spk if not(utt_id in utt_ids)]

        corpus = self.subcorpus(kept_utts, validate=False)
        corpus.lexicon = {
            key: value for key, value in corpus.lexicon.items()
            if not(key in words)}

        corpus.phones = {
            key: value for key, value in corpus.phones.items()
            if not(key in phones)}

        corpus.silences = [
            value for value in corpus.silences if not(value in silences)]

        return corpus

    def split(self, train_prop=None, test_prop=None,
              by_speakers=True, random_seed=None):
        """Split a corpus in train and testing subcorpora

        Return a pair (train, testing) of Corpus instances, validated
        and pruned.

        test_prop : float, should be between 0.0 and 1.0 and
          represent the proportion of the dataset to include in the
          test split. If None, the value is automatically set to the
          complement of the train size. If train size is also None,
          test size is set to 0.5 (default is None).

        train_prop : float, should be between 0.0 and 1.0 and
          represent the proportion of the dataset to include in the
          train split. If None, the value is automatically set to the
          complement of the test size (default is None).

        by_speakers : bool, split the corpus by speakers if True, else
          split by utterances (regardless of speakers distribution).
          Note that this might not be appropriate when the amount of
          utterances available per speaker is too unbalanced (default
          is True).

        random_seed : seed for pseudo-random numbers generation (default
          is to use the current system time)

        """
        spliter = CorpusSplit(self, random_seed=random_seed, prune=True)
        split_fun = (spliter.split if by_speakers is False
                     else spliter.split_by_speakers)
        return split_fun(train_prop, test_prop)

    def phonemize(self):
        """Return a phonemized version of the corpus

        All the word related data is removed from the original
        corpus. Lexicon becomes a mapping phone -> phone and the text
        is phonemized (see the phonemize_text method).

        The returned corpus have same wavs, segments, utt2spk, phones,
        silences and variants than the original "word" corpus.

        """
        corpus = Corpus()
        corpus.meta.source = self.meta.source
        corpus.meta.name = 'phonemized version of ' + self.meta.name
        corpus.wav_folder = self.wav_folder
        corpus.wavs = self.wavs
        corpus.segments = self.segments
        corpus.phones = self.phones
        corpus.utt2spk = self.utt2spk
        corpus.silences = self.silences
        corpus.variants = self.variants
        corpus.lexicon = {p: p for p in corpus.phones.keys()}
        corpus.text = self.phonemize_text()
        return corpus

    def phonemize_text(self):
        """Return a phonemized version of self.text

        Transcription of a corpus text directly into phones, without any
        word boundary marker. This is used to estimate phone-level n-gram
        language models for use with kaldi recipes.

        For OOVs: replace it by <unk>

        """
        phonemized = dict()
        for utt_id, text in self.text.items():
            phones = []
            for word in text.split():
                try:
                    phones.append(self.lexicon[word])
                except KeyError:
                    # OOV: for now we replace the word by <unk>
                    phones.append(self.lexicon['<unk>'])
            phonemized[utt_id] = ' '.join(phones)
        return phonemized

    def plot(self):
        """Plot the distribution of speech duration for each speaker"""
        # last moment import because this causes errors as
        # "QXcbConnection: Could not connect to display" when running
        # on a session without graphical support (e.g. a ssh
        # connection without X forward)
        import matplotlib.pyplot as plt

        utt_ids, utt_speakers = zip(*self.utt2spk.items())
        utt2dur = self.utt2duration()
        spkr2dur = dict()

        for spkr in utt_speakers:
            spkr2dur[spkr] = sum(
                [utt2dur[utt_id] for utt_id in self.utt2spk
                 if self.utt2spk[utt_id] == spkr])

        sorted_speaker = sorted(spkr2dur.items(), key=lambda k, v: (v, k))
        sorted_speaker.reverse()

        # Set plot parameters
        names = [spk_id for (spk_id, duration) in sorted_speaker]
        times = [duration for (spk_id, duration) in sorted_speaker]
        times_in_minutes = [format(u0 / 60, '.1f') for u0 in times]
        font = {'weight': 'bold',
                'size': 15}
        plt.rc('font', **font)

        # Get corpus duration
        # total = self.duration(format='seconds')
        # (spk_id0, duration0) = sorted_speaker[0]
        x_axis = range(0, len(names))

        # Set barplot
        # barlist = plt.bar(
        #     x_axis, times, width=0.7,
        #     align="center", label="speech time", color="blue")
        self.log.info('Speech duration for corpus : %i minutes', sum(times)/60)

        for j, txt in enumerate(times_in_minutes):
            # add legends and annotation to plot
            plt.annotate(txt, (x_axis[j], times[j]+3), rotation=45)
            plt.legend()
            plt.xticks(x_axis, names, rotation=45)
            plt.xlabel('speaker')
            plt.ylabel('duration (in minutes)', rotation=90)

        return(plt)

    def merge_wavs(self, output_dir, log=None, padding=0.):
        """ Merge all wav files from same speaker
        Returns a corpus with one wav file per speaker """
        if log is None:
            log = self.log
        CorpusMergeWavs(self, log=log).merge_wavs(output_dir, padding)

    def create_filter(self, out_path, function,
                      nb_speaker=None, new_speakers=10, THCHS30=False):
        """Filter the speech duration distribution of the corpus"""
        return(CorpusFilter(self).create_filter(
            out_path, function, nb_speaker, new_speakers, THCHS30))

    def trim(self, corpus_dir, output_dir, function, not_kept_utts):
        """ Remove utterances from the corpus
            (using sox to trim the wav files)"""
        CorpusTrimmer(self).trim(
                corpus_dir, output_dir, function, not_kept_utts)
