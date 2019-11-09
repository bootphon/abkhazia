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
"""Test of the Corpus class"""

import os
from abkhazia.corpus import Corpus

import pytest


@pytest.mark.parametrize('copy_wavs', [True, False])
def test_save_corpus(tmpdir, corpus, copy_wavs):
    assert corpus.is_valid()
    corpus_saved = str(tmpdir.mkdir('corpus-{}'.format(copy_wavs)))
    corpus.save(corpus_saved, copy_wavs=copy_wavs)
    assert os.path.isfile(os.path.join(corpus_saved, 'meta.txt'))

    d = Corpus.load(corpus_saved)
    assert d.is_valid()
    assert corpus.lexicon == d.lexicon
    assert corpus.segments == d.segments
    assert corpus.phones == d.phones
    assert corpus.wavs == d.wavs


def test_empty():
    c = Corpus()
    assert not c.is_valid()
    assert c.spk2utt() == {}
    assert len(c.utts()) == 0


def test_subcorpus(corpus):
    d = corpus.subcorpus(list(corpus.utts())[:5])
    assert '<unk>' in d.lexicon
    assert len(d.utts()) == 5
    assert d.is_valid()

    e = corpus.subcorpus(list(corpus.utts())[:5], prune=False)
    assert len(e.utts()) == 5
    assert e.is_valid()

    assert len(d.wavs) <= len(e.wavs)
    for w in d.wavs:
        assert w in e.wavs
    assert d.wav_folder == e.wav_folder


def test_split(corpus):
    d, e = corpus.split(train_prop=0.5)
    assert '<unk>' in d.lexicon
    assert '<unk>' in e.lexicon

    assert len(corpus.lexicon) >= len(d.lexicon)
    assert len(corpus.utts()) > len(e.utts())
    assert len(corpus.utts()) > len(d.utts())
    assert len(set.intersection(set(d.utts()), set(e.utts()))) == 0
    assert len(set.intersection(set(d.spks()), set(e.spks()))) >= 0
    assert len(set.intersection(set(corpus.utts()), set(e.utts()))) == \
        len(e.utts())


def test_split_tiny_train(corpus):
    with pytest.raises(IOError) as err:
        train, testing = corpus.split(train_prop=0.25, by_speakers=False)
    assert 'corpus is empty' in str(err.value)

    train, testing = corpus.split(train_prop=0.4, by_speakers=False)
    assert len(train.utts()) <= len(testing.utts())
    assert len(train.spks()) == len(testing.spks())

    train, testing = corpus.split(train_prop=0.4, by_speakers=True)
    assert len(train.utts()) < len(testing.utts())
    assert len(train.spks()) < len(testing.spks())


def test_split_by_speakers(corpus):
    d, e = corpus.split(0.5, by_speakers=True)

    assert len(corpus.utts()) > len(e.utts())
    assert len(corpus.utts()) > len(d.utts())
    assert len(set.intersection(set(d.utts()), set(e.utts()))) == 0
    assert len(set.intersection(set(d.spks()), set(e.spks()))) == 0
    assert len(set.intersection(set(corpus.utts()), set(e.utts()))) == \
        len(e.utts())


@pytest.mark.parametrize('copy_wavs', [True, False])
def test_split_and_save(corpus, copy_wavs, tmpdir):
    a, b = corpus.split(train_prop=0.25)
    a.save(str(tmpdir.mkdir('a')), copy_wavs=copy_wavs)
    b.save(str(tmpdir.mkdir('b')), copy_wavs=copy_wavs)


@pytest.mark.parametrize('by_speaker', [True, False])
def test_split_less_than_1(corpus, by_speaker):
    d, e = corpus.split(0.4, 0.5, by_speaker)

    assert len(d.utts()) + len(e.utts()) <= len(corpus.utts())
    assert len(d.utts()) > 0
    assert len(e.utts()) > 0

    # very low proportion -> the resulting corpus is empty
    if by_speaker is False:
        with pytest.raises(IOError) as err:
            train, testing = corpus.split(0.25, 0.5, by_speaker)
        assert 'corpus is empty' in str(err.value)

    with pytest.raises(IOError) as err:
        d, _ = corpus.split(1e-30)
    assert 'corpus is empty' in str(err.value)


def test_spk2utt():
    c = Corpus()
    c.utt2spk = {'u1': 's1', 'u2': 's1', 'u3': 's2'}
    assert c.spk2utt() == {'s1': ['u1', 'u2'], 's2': ['u3']}


def test_phonemize_text(corpus, tmpdir):
    phones = corpus.phonemize_text()
    assert sorted(phones.keys()) == sorted(corpus.utts())
    assert len(phones) == len(corpus.text)


def test_phonemize_corpus(corpus):
    c = corpus.phonemize()
    assert c.is_valid()
    assert all([k == v for k, v in c.lexicon.items() if k != '<unk>'])
    assert len(c.lexicon) == len(c.phones) + 1  # <unk>


def test_remove_phones(corpus):
    def _aux(p, d):
        for v in d.values():
            if p in v:
                return True
        return False

    # get a phone
    p = list(corpus.phones.keys())[0]

    # make sure the phone is here
    assert p in corpus.phones
    assert _aux(p, corpus.lexicon)

    # remove phone from corpus
    corpus = corpus.remove_phones(phones=[p])

    # make sure the phone is not here
    assert p not in corpus.phones
    assert not _aux(p, corpus.lexicon)
