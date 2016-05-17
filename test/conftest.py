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

HERE = os.path.abspath(os.path.dirname(__file__))


@pytest.yield_fixture(scope='session')
def corpus():
    """Return a corpus made of 100 random utts of Buckeye

    This little corpus is the base of all corpus dependant tests.

    The fixture assumes corpus/buckeye-directory is defined in the
    abkhazia configuration file.

    """
    # prepare the whole buckeye corpus
    b = utils.config.get('corpus', 'buckeye-directory')
    p = os.path.join(HERE, 'prepared_wavs')
    c = BuckeyePreparator(b).prepare(p)

    # select 100 random utterances
    u = c.utts()
    random.shuffle(u)

    try:
        c.save(os.path.join(HERE, 'data'))
    except:
        pass

    yield c.subcorpus(u[:100])
    utils.remove(p, safe=True)
