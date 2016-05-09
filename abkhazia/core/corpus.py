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

    def save(self, path, copy_wavs=False):
        """Save the corpus to the directory `path`

        `path` is assumed to be a non existing directory.

        If `copy_wavs` if True, force a file copy, else use symlinks.

        """
        corpus_saver.CorpusSaver.save(self, path, copy_wavs=copy_wavs)

    def validate(self,
                 njobs=utils.default_njobs(),
                 log=utils.log2file.null_logger()):
        """Validate speech corpus data

        Raise on the first encoutered error, relies on the
        CorpusValidation class.

        """
        corpus_validation.CorpusValidation(njobs, log).validate(self)

    def spk2utt(self):
        """Return a dict of speakers mapped to an utterances list

        Built from self.utt2spk. This is a Python implementation of
        Kaldi egs/wsj/s5/utils/utt2spk_to_spk2utt.pl.

        """
        spk2utt = {spk: [] for spk in set(self.utt2spk.itervalues())}
        for utt, spk in self.utt2spk.iteritems():
            spk2utt[spk].append(utt)
        return spk2utt
