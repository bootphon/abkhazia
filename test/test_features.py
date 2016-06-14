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
"""Test of features extraction"""

import os
import pytest

import abkhazia.models.features as features
import abkhazia.utils as utils
from .conftest import assert_no_expr_in_log


@pytest.mark.parametrize('pitch', [True, False])
def test_features(pitch, corpus, tmpdir):
    output_dir = str(tmpdir.mkdir('feats'))
    flog = os.path.join(output_dir, 'feats.log')
    log = utils.get_log(flog)

    # keep only 1 utterance for testing speed
    subcorpus = corpus.subcorpus(corpus.utts()[:1])
    feat = features.Features(subcorpus, output_dir, log=log)
    feat.njobs = 1
    feat.use_pitch = pitch
    feat.create()
    feat.run()
    feat.export()
    assert_no_expr_in_log(flog, 'error')
    assert os.path.isfile(os.path.join(output_dir, 'meta.txt'))
