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
"""Test of the abkhazia.models.language_model module"""

import os
import pytest

import abkhazia.language.language_model as language_model
import abkhazia.utils as utils
import abkhazia.kaldi as kaldi
from .conftest import assert_no_expr_in_log


levels = ['phone', 'word']
orders = range(1, 4)
params = [(l, o) for l in levels for o in orders]


def test_srilm_path():
    # test we can reach the ngram binary from SRILM in the Kaldi
    # environment (problematic because it's change from Linux to Mac)
    # This raises RuntimeError if failing
    utils.jobs.run('which ngram', env=kaldi.path.kaldi_path())


@pytest.mark.parametrize('level, order', params)
def test_lm(level, order, corpus, tmpdir):
    output_dir = str(tmpdir.mkdir('lang'))
    flog = os.path.join(output_dir, 'language.log')
    log = utils.logger.get_log(flog)
    lm = language_model.LanguageModel(corpus, output_dir, log=log)
    lm.level = level
    lm.order = order
    lm.create()
    lm.run()
    lm.export()
    language_model.check_language_model(output_dir)
    assert_no_expr_in_log(flog, 'error')


@pytest.mark.parametrize('prob', [0, 0.5])
def test_silence_probability(prob, corpus, tmpdir):
    output_dir = str(tmpdir.mkdir('lang'))
    flog = os.path.join(output_dir, 'language.log')
    log = utils.logger.get_log(flog)
    lm = language_model.LanguageModel(corpus, output_dir, log=log)
    lm.level = 'word'
    lm.order = 3
    lm.silence_probability = prob
    lm.create()
    lm.run()
    lm.export()
    language_model.check_language_model(output_dir)
    assert_no_expr_in_log(flog, 'error')
