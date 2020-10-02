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


expected_ali = {
    'words': [
        "s0102a-sent17 0.3675 1.9275 that's",
        "s0102a-sent17 3.0275 3.1975 what",
        "s0102a-sent17 3.1975 3.2275 i",
        "s0102a-sent17 3.2275 3.3875 <SIL>",
        "s0102a-sent17 3.3875 3.5075 <NOISE>",
        "s0102a-sent17 3.5075 4.4075 recall",
        "s0102a-sent17 4.4075 6.1975 missing",
        "s0102a-sent17 6.1975 6.3275 <SIL>",
        "s0102a-sent17 6.3275 6.6550 <IVER>"],
    'phones': [
        's0102a-sent17 0.0000 0.3675 SIL',
        "s0102a-sent17 0.3675 0.5675 dh",
        "s0102a-sent17 0.5675 0.7675 ae",
        "s0102a-sent17 0.7675 0.7975 t",
        "s0102a-sent17 0.7975 1.9275 s",
        "s0102a-sent17 1.9275 3.0275 SIL",
        "s0102a-sent17 3.0275 3.0575 w",
        "s0102a-sent17 3.0575 3.0875 ah",
        "s0102a-sent17 3.0875 3.1975 t",
        "s0102a-sent17 3.1975 3.2275 ah",
        "s0102a-sent17 3.2275 3.3875 SIL",
        "s0102a-sent17 3.3875 3.5075 NSN",
        "s0102a-sent17 3.5075 3.7175 r",
        "s0102a-sent17 3.7175 3.8475 iy",
        "s0102a-sent17 3.8475 4.2075 k",
        "s0102a-sent17 4.2075 4.3575 ao",
        "s0102a-sent17 4.3575 4.4075 l",
        "s0102a-sent17 4.4075 4.4375 m",
        "s0102a-sent17 4.4375 4.4875 ih",
        "s0102a-sent17 4.4875 5.1975 s",
        "s0102a-sent17 5.1975 6.1675 iy",
        "s0102a-sent17 6.1675 6.1975 n",
        "s0102a-sent17 6.1975 6.3275 SIL",
        "s0102a-sent17 6.3275 6.6550 NSN"],
    'both': [
        's0102a-sent17 0.0000 0.3675 SIL',
        "s0102a-sent17 0.3675 0.5675 dh that's",
        "s0102a-sent17 0.5675 0.7675 ae",
        "s0102a-sent17 0.7675 0.7975 t",
        "s0102a-sent17 0.7975 1.9275 s",
        "s0102a-sent17 1.9275 3.0275 SIL",
        "s0102a-sent17 3.0275 3.0575 w what",
        "s0102a-sent17 3.0575 3.0875 ah",
        "s0102a-sent17 3.0875 3.1975 t",
        "s0102a-sent17 3.1975 3.2275 ah i",
        "s0102a-sent17 3.2275 3.3875 SIL <SIL>",
        "s0102a-sent17 3.3875 3.5075 NSN <NOISE>",
        "s0102a-sent17 3.5075 3.7175 r recall",
        "s0102a-sent17 3.7175 3.8475 iy",
        "s0102a-sent17 3.8475 4.2075 k",
        "s0102a-sent17 4.2075 4.3575 ao",
        "s0102a-sent17 4.3575 4.4075 l",
        "s0102a-sent17 4.4075 4.4375 m missing",
        "s0102a-sent17 4.4375 4.4875 ih",
        "s0102a-sent17 4.4875 5.1975 s",
        "s0102a-sent17 5.1975 6.1675 iy",
        "s0102a-sent17 6.1675 6.1975 n",
        "s0102a-sent17 6.1975 6.3275 SIL <SIL>",
        "s0102a-sent17 6.3275 6.6550 NSN <IVER>"]}


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

        if not post:
            res = [l.strip() for l in utils.open_utf8(ali_file, 'r')
                   if l.startswith('s0102a-sent17')]
            assert res == expected_ali[level]
