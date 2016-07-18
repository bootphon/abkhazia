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
"""Test of the abkhazia.models.acoustic_model module"""

import os
import sys
import pytest

import abkhazia.models.acoustic_model as acoustic_model
import abkhazia.utils as utils
from .conftest import assert_no_expr_in_log


@pytest.mark.parametrize('njobs', [1, 2, 4])
def test_acoustic_njobs(corpus, features, language_model, njobs, tmpdir):
    output_dir = str(tmpdir.mkdir('lang'))
    flog = os.path.join(output_dir, 'language.log')
    log = utils.get_log(flog)
    am = acoustic_model.AcousticModel(corpus, output_dir, log)

    am.feat = features
    am.lang = language_model
    am.njobs = njobs
    am.model_type = 'mono'
    am.num_gauss_si = 10
    am.num_states_si = 10
    am.num_gauss_sa = 10
    am.num_states_sa = 10

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

    acoustic_model.check_acoustic_model(output_dir)
    assert_no_expr_in_log(flog, 'error')
