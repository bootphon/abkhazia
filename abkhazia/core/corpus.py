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
        self.wavs = None
        self.lexicon = None
        self.segments = None
        self.text = None
        self.phones = None
        self.silences = None
        self.utt2spk = None
        self.variants = None

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
