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
"""Test of the Corpus class"""

import os
from abkhazia.core.corpus import Corpus

HERE = os.path.abspath(os.path.dirname(__file__))
corpus_dir = os.path.join(HERE, 'data')


def test_corpus(tmpdir):
    c = Corpus.load(corpus_dir)
    assert c.is_valid()

    corpus_saved = os.path.join(str(tmpdir), 'corpus')
    c.save(corpus_saved)

    d = Corpus.load(corpus_saved)
    assert d.is_valid()
    assert c.lexicon == d.lexicon
    assert c.wavs == d.wavs
    assert c.segments == d.segments
    assert c.phones == d.phones


def test_empty():
    c = Corpus()
    assert not c.is_valid()
    assert c.spk2utt() == {}
    assert len(c.utts()) == 0


def test_subcorpus():
    c = Corpus.load(corpus_dir)
    d = c.subcorpus(c.utts()[:10])
    assert len(d.utts()) == 10
    assert d.is_valid()


def test_spk2utt():
    c = Corpus()
    c.utt2spk = {'u1': 's1', 'u2': 's1', 'u3': 's2'}
    assert c.spk2utt() == {'s1': ['u1', 'u2'], 's2': ['u3']}
