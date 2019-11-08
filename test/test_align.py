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


expected_ali = [
    "s0102a-sent16 0.5875 0.9175 so",
    "s0102a-sent16 0.9175 2.5875 i",
    "s0102a-sent16 2.5875 0.1775 think",
    "s0101b-sent24 0.1775 0.4975 i've",
    "s0101b-sent24 0.4975 0.5575 heard",
    "s0101b-sent24 0.5575 0.6875 some",
    "s0101b-sent24 0.6875 0.9675 of",
    "s0101b-sent24 0.9675 1.2675 them",
    "s0101b-sent24 1.2675 1.4875 talk",
    "s0101b-sent24 1.4875 1.8875 about",
    "s0101b-sent24 1.8875 0.1875 it",
    "s0102b-sent19 0.1875 0.2175 <VOCNOISE>",
    "s0102b-sent19 0.2175 0.9575 that",
    "s0101b-sent23 0.9575 0.3675 personally",
    "s0102a-sent17 0.3675 3.0275 that's",
    "s0102a-sent17 3.0275 3.1975 what",
    "s0102a-sent17 3.1975 3.2275 i",
    "s0102a-sent17 3.2275 3.3875 <SIL>",
    "s0102a-sent17 3.3875 3.5075 <NOISE>",
    "s0102a-sent17 3.5075 4.4075 recall",
    "s0102a-sent17 4.4075 6.1975 missing"]

params = [(l, p) for l in ('phones', 'words', 'both') for p in (True, False)]


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

    if level == 'words' and post:
        with pytest.raises(NotImplementedError):
            aligner.compute()
    else:
        aligner.compute()

        # check if we have no error and an alignment file
        assert_no_expr_in_log(flog, 'error')
        ali_file = os.path.join(output_dir, 'alignment.txt')
        assert os.path.isfile(ali_file)

        # # TODO fix that bug, the following assert must pass!
        # if level == 'words' and not post:
        #     res = [l.strip() for l in utils.open_utf8(ali_file, 'r')]
        #     assert res == expected_ali
