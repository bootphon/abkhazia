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
"""Provides the Corpus class"""

import abkhazia.core.corpus_validation as corpus_validation
import abkhazia.core.corpus_loader as corpus_loader
import abkhazia.core.corpus_saver as corpus_saver
import abkhazia.utils as utils


class Corpus(object):
    """Speech corpus in the abkhazia format

    TODO comment on attributes (exact type and content exemple)
    TODO meta.txt with metainfo -> (name, creation date, source)

    """

    @classmethod
    def load(cls, corpus_dir):
        """Return a corpus initialized from `corpus_dir`

        Raise IOError if corpus_dir if an invalid abkhazia corpus
        directory.

        """
        return corpus_loader.CorpusLoader.load(cls, corpus_dir)

    def __init__(self):
        """Init an empty corpus"""
        self.wavs = dict()
        self.lexicon = dict()
        self.segments = dict()
        self.text = dict()
        self.phones = dict()
        self.utt2spk = dict()
        self.silences = []
        self.variants = []

    def save(self, path, no_wavs=False):
        """Save the corpus to the directory `path`

        `path` is assumed to be a non existing directory.

        If `no_wavs` if True, dont save the wavs (ie don't write wavs
        subdir)

        """
        corpus_saver.CorpusSaver.save(self, path, no_wavs=no_wavs)

    def validate(self,
                 njobs=utils.default_njobs(),
                 log=utils.log2file.null_logger()):
        """Validate speech corpus data

        Raise on the first encoutered error, relies on the
        CorpusValidation class.

        """
        corpus_validation.CorpusValidation(
            self, njobs=njobs, log=log).validate()

    def is_valid(self, njobs=utils.default_njobs()):
        """Return True if the corpus is validated, False else"""
        try:
            self.validate()
        except:
            return False
        return True

    def utts(self):
        """Return the list of utterance ids stored in the corpus"""
        return self.utt2spk.keys()

    def spk2utt(self):
        """Return a dict of speakers mapped to an utterances list

        Built from self.utt2spk. This method is a Python
        implementation of the Kaldi script
        egs/wsj/s5/utils/utt2spk_to_spk2utt.pl.

        """
        # init an empty list for all speakers
        spk2utt = {spk: [] for spk in set(self.utt2spk.itervalues())}

        # populate lists with utterance ids
        for utt, spk in self.utt2spk.iteritems():
            spk2utt[spk].append(utt)
        return spk2utt

    def wav2utt(self):
        """Return a dict of wav ids mapped to utterances/timestamps they contain

        The values of the returned dict are tuples (utt-id, tstart,
        tend). Built on self.segments.

        """
        # init an empty list for all wavs
        wav2utt = {wav: [] for wav, _, _ in self.segments.itervalues()}

        # populate lists with utterance ids and timestamps
        for utt, (wav, tstart, tend) in self.segments.iteritems():
            wav2utt[wav].append((utt, float(tstart), float(tend)))
        return wav2utt

    def utt2duration(self):
        """Return a dict of utterances ids mapped to their duration (in s.)"""
        d = dict()
        for utt, (wav, start, stop) in self.segments.iteritems():
            start = 0 if start is None else start
            stop = utils.wav.duration(wav) if stop is None else stop
            d[utt] = stop - start
        return d

    def has_several_utts_per_wav(self):
        """Return True if there is several utterances on each wav file"""
        for _, start, stop in self.segments.itervalues():
            if start is not None or stop is not None:
                return True
        return False

    def subcorpus(self, utt_ids, validate=False):
        """Return a subcorpus made of utterances in `utt_ids`

        Each utterance in `utt_ids` is assumed to be part of self,
        else a KeyError is raised.

        Raise if the subcorpus is not valid.

        """
        corpus = Corpus()
        corpus.wavs = self.wavs
        corpus.lexicon = self.lexicon
        corpus.phones = self.phones
        corpus.silences = self.silences
        corpus.variants = self.variants

        corpus.segments = dict()
        corpus.text = dict()
        corpus.utt2spk = dict()
        for utt in utt_ids:
            corpus.segments[utt] = self.segments[utt]
            corpus.text[utt] = self.text[utt]
            corpus.utt2spk[utt] = self.utt2spk[utt]

        if validate:
            corpus.validate()
        return corpus
