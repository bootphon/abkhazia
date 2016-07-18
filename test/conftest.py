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
"""Abkhazia test setup"""

import os
import random
import re

import pytest

import abkhazia.utils as utils
from abkhazia.prepare import BuckeyePreparator
from abkhazia.corpus import Corpus
from abkhazia.models.features import Features
from abkhazia.models.language_model import LanguageModel

HERE = os.path.abspath(os.path.dirname(__file__))


@pytest.yield_fixture(scope='session')
def corpus(n=50):
    """Return a corpus made of `n` random utts of Buckeye

    This little corpus is the base of all corpus dependant tests. The
    session scope ensures the corpus is initialized only once for all
    the tests.

    The fixture assumes corpus/buckeye-directory is defined in the
    abkhazia configuration file or, if already prepared, that
    abkhazia/data-directory if defined and have the Buckeye corpus
    prepared in its buckeye/data subfolder.

    """
    try:
        tmpdir = os.path.join(HERE, 'prepared_wavs')

        # first try to load any prepared buckeye
        buckeye = os.path.join(
            utils.config.get('abkhazia', 'data-directory'),
            'buckeye', 'data')
        if os.path.isdir(buckeye):
            corpus = Corpus.load(buckeye)

        else:  # prepare the whole buckeye corpus
            buckeye = utils.config.get('corpus', 'buckeye-directory')
            corpus = BuckeyePreparator(buckeye).prepare(tmpdir)
            corpus.validate()

        # select n random utterances from the whole buckeye, take the
        # whole if n is 0
        if n != 0:
            utts = corpus.utts()
            random.shuffle(utts)
            subcorpus = corpus.subcorpus(utts[:n])
        else:
            subcorpus = corpus
        yield subcorpus

    finally:
        # remove any prepared wavs
        utils.remove(tmpdir, safe=True)


@pytest.fixture(scope='session')
def features(corpus, tmpdir_factory):
    """Return a directory with MFCC features computed from the test corpus"""
    output_dir = str(tmpdir_factory.mktemp('features'))
    feat = Features(corpus, output_dir)
    feat.use_pitch = False
    feat.use_cmvn = True
    feat.delta_order = 0
    feat.compute()
    return output_dir


@pytest.fixture(scope='session')
def language_model(corpus, tmpdir_factory):
    """Return a directory with bigram word LM computed from the test corpus"""
    output_dir = str(tmpdir_factory.mktemp('lm'))
    flog = os.path.join(output_dir, 'language.log')
    log = utils.get_log(flog)
    lm = LanguageModel(corpus, output_dir, log=log)
    lm.level = 'word'
    lm.order = 2
    lm.compute()
    return output_dir


def assert_no_expr_in_log(flog, expr='error'):
    assert os.path.isfile(flog)

    matched_lines = [line for line in open(flog, 'r')
                     if re.search(expr, line.lower())]

    if matched_lines:
        print matched_lines
    assert len(matched_lines) == 0
