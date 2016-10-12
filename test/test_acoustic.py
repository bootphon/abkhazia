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
"""Test of the abkhazia.models.acoustic module"""

import os
import sys
import pytest

import abkhazia.models.acoustic as acoustic
import abkhazia.utils as utils
from .conftest import assert_no_expr_in_log, assert_expr_in_log


# There was a bug with more than 9 jobs (when more than 9 available
# cores/nodes)
@pytest.mark.parametrize('njobs', [4, 11])
def test_acoustic_njobs(corpus, features, lm_word, njobs, tmpdir):
    output_dir = str(tmpdir.mkdir('am-mono'))
    flog = os.path.join(output_dir, 'am-mono.log')
    log = utils.logger.get_log(flog)
    am = acoustic.Monophone(corpus, lm_word, features, output_dir, log)

    am.njobs = njobs
    am.options['total-gaussians'].value = 10
    am.options['num-iterations'].value = 2
    am.options['realign-iterations'].value = [1]

    try:
        am.compute()
    except RuntimeError as err:
        # dump the log to stdout
        sys.stdout.write('####################\n')
        sys.stdout.write(open(flog, 'r').read())
        # log_inner = os.path.join(
        #     output_dir, 'recipe/exp/mono/log/align.0.14.log')
        # sys.stdout.write(open(log_inner, 'r').read())
        sys.stdout.write('####################\n')
        raise err

    acoustic.check_acoustic_model(output_dir)
    assert acoustic.model_type(output_dir) == 'mono'
    assert str(am.options['num-iterations']) == '2'
    assert_expr_in_log(flog, ' --num-iters 2 ')
    assert_no_expr_in_log(flog, 'error')
