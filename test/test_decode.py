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
"""Test of the abkhazia.decode module"""

import os
import pytest

import abkhazia.decode as decode
import abkhazia.utils as utils

from .conftest import assert_no_expr_in_log


#
# Basic tests, decode a single utterance from the train corpus. Uses
# all the levels of acoustic models.
#


def wrapper_test_decode(name, options, corpus, lm, feats, am, tmpdir,
                        skip_scoring=False):
    # decode only the first utterance (just make the test faster)
    corpus = corpus.subcorpus([corpus.utts()[0]])
    output_dir = str(tmpdir.mkdir('decode-{}'.format(name)))
    flog = os.path.join(output_dir, 'decode-{}.log'.format(name))

    decoder = decode.Decode(
        corpus, lm, feats, am, output_dir, log=utils.logger.get_log(flog))
    for k, v in options.items():
        decoder.decode_opts[k].value = v
    if skip_scoring:
        decoder.score_opts['skip-scoring'] = True
    decoder.compute()

    # check if we have no error in log
    assert_no_expr_in_log(flog, 'error')

    # check we have word error rates if scoring
    scoring = os.path.isfile(
        os.path.join(output_dir, 'scoring_kaldi', 'best_wer'))
    assert scoring if not skip_scoring else not scoring


@pytest.mark.parametrize('skip_scoring', [True, False])
def test_decode_mono(
        corpus, lm_word, features, am_mono, tmpdir, skip_scoring):
    options = {'max-active': 5, 'beam': 2, 'lattice-beam': 1}
    wrapper_test_decode(
        'mono', options, corpus, lm_word, features, am_mono,
        tmpdir, skip_scoring)


@pytest.mark.parametrize('skip_scoring', [True, False])
def test_decode_tri(
        corpus, lm_word, features, am_tri, tmpdir, skip_scoring):
    options = {'max-active': 5, 'beam': 2, 'lattice-beam': 1}
    wrapper_test_decode(
        'tri', options, corpus, lm_word, features, am_tri,
        tmpdir, skip_scoring)


@pytest.mark.parametrize('skip_scoring', [True, False])
def test_decode_trisa(
        corpus, lm_word, features, am_trisa, tmpdir, skip_scoring):
    options = {'max-active': 2, 'beam': 1, 'lattice-beam': 1,
               'first-beam': 1, 'first-max-active': 2}
    wrapper_test_decode(
        'trisa', options, corpus, lm_word, features, am_trisa,
        tmpdir, skip_scoring)


@pytest.mark.parametrize('skip_scoring', [True, False])
def test_decode_nnet(
        corpus, lm_word, features, am_nnet, tmpdir, skip_scoring):
    options = {'min-active': 1, 'max-active': 2, 'beam': 2, 'lattice-beam': 1}
    wrapper_test_decode(
        'nnet', options, corpus, lm_word, features, am_nnet,
        tmpdir, skip_scoring)


#
# Tests using separate corpora or crossing LM/AM
#


# LM and AM from corpus1, decode corpus2
def test_decode_corpus2(corpus2, features2, am_mono, lm_word, tmpdir):
    wrapper_test_decode(
        'corpus2', {'max-active': 15, 'beam': 3, 'lattice-beam': 2},
        corpus2, lm_word, features2, am_mono, tmpdir)


# AM from corpus1, LM from corpus2, decode corpus2
def test_crossing_lm_am(corpus2, features2, am_mono, lm_word2, tmpdir):
    wrapper_test_decode(
        'lmam', {'max-active': 15, 'beam': 3, 'lattice-beam': 2},
        corpus2, lm_word2, features2, am_mono, tmpdir)
