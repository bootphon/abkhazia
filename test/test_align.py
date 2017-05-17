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
"""Test of the abkhazia.align module"""

import os
import pytest
import abkhazia.align as align
from abkhazia import utils
from .conftest import assert_no_expr_in_log


# params = [(l, p) for l in ('phones', 'words', 'both') for p in (True, False)]
params = [('both', False)]


@pytest.mark.parametrize('level, post', params)
def test_align(
        corpus, features, lm_word, am_mono, tmpdir, level, post):
    output_dir = str(tmpdir.mkdir('align-phones'))
    flog = os.path.join(output_dir, 'align-phones.log')
    log = utils.logger.get_log(flog)

    aligner = align.Align(corpus, output_dir=output_dir, log=log)
    aligner.feat_dir = features
    aligner.lm_dir = lm_word
    aligner.am_dir = am_mono
    aligner.level = level
    aligner.with_posteriors = post
    aligner.compute()

    # check if we have no error and an alignment file
    assert_no_expr_in_log(flog, 'error')
    assert os.path.isfile(
        os.path.join(output_dir, 'alignment.txt'))
