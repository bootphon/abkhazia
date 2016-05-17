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
import pytest
import random

import abkhazia.utils as utils
from abkhazia.prepare import BuckeyePreparator
from abkhazia.corpus import Corpus

HERE = os.path.abspath(os.path.dirname(__file__))


@pytest.yield_fixture(scope='session')
def corpus():
    """Return a corpus made of 100 random utts of Buckeye

    This little corpus is the base of all corpus dependant tests. The
    session scope ensures the corpus is initialized only once for all
    the tests.

    The fixture assumes corpus/buckeye-directory is defined in the
    abkhazia configuration file or, if already prepared, that
    abkhazia/data-directory if defined and have the Buckeye corpus
    prepared in its buckeye/data subfolder.

    """
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

    # select 100 random utterances from the whole buckeye
    utts = corpus.utts()
    random.shuffle(utts)
    subcorpus = corpus.subcorpus(utts[:100])

    # save it to test/data
    try:
        subcorpus.save(os.path.join(HERE, 'data'))
    except OSError:  # already existing
        pass

    yield subcorpus

    # remove any prepared wavs
    utils.remove(tmpdir, safe=True)
