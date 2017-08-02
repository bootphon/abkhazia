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
"""Test of the abkhazia.language.language_model module"""

import os
import pytest

import abkhazia.language.language_model as language_model
import abkhazia.utils as utils
import abkhazia.kaldi as kaldi
from .conftest import assert_no_expr_in_log


levels = ['phone', 'word']
orders = range(1, 4)
wpd = [False, True]
params = [(l, o, w) for l in levels for o in orders for w in wpd]


def test_srilm_path():
    # test we can reach the ngram binary from SRILM in the Kaldi
    # environment (problematic because it's change from Linux to Mac)
    # This raises RuntimeError if failing
    utils.jobs.run('which ngram', env=kaldi.path.kaldi_path())


@pytest.mark.parametrize('level, order, wpd', params)
def test_lm(level, order, wpd, corpus, tmpdir):
    output_dir = str(tmpdir.mkdir('lang'))
    flog = os.path.join(output_dir, 'language.log')
    log = utils.logger.get_log(flog)
    lm = language_model.LanguageModel(corpus, output_dir, log=log)
    lm.level = level
    lm.order = order
    lm.position_dependent_phones = wpd
    lm.create()

    print('environ ' + str(len(os.environ)))
    lm.run()
    print('environ ' + str(len(os.environ)))
    lm.export()

    # check the excpeted files are here
    language_model.check_language_model(output_dir)

    # no error in log
    assert_no_expr_in_log(flog, 'error')

    # phone_map.txt is here
    phonemap = os.path.join(output_dir, 'local', 'phone_map.txt')
    assert os.path.isfile(phonemap)

    # all the phones in the corpus are in phonemap
    phonemap = [l.strip().split() for l in utils.open_utf8(phonemap, 'r')]
    phonemap = {l[0]: l[1:] for l in phonemap}
    assert all(p in phonemap.keys() for p in corpus.phones.keys())

    # 1 or 4/5 rows according to word position dependant phones
    if wpd:
        assert all(len(p) >= 4 and len(p) < 6 for p in phonemap.values())
    else:
        assert all(len(p) == 1 for p in phonemap.values())


@pytest.mark.parametrize('prob', [0, 0.5, 0.99, 1, 1.1])
def test_silence_probability(prob, corpus, tmpdir):
    output_dir = str(tmpdir.mkdir('lang'))
    flog = os.path.join(output_dir, 'language.log')
    log = utils.logger.get_log(flog)
    lm = language_model.LanguageModel(corpus, output_dir, log=log)
    lm.level = 'word'
    lm.order = 2
    lm.silence_probability = prob

    if prob >= 1 or prob < 0:
        with pytest.raises(RuntimeError):
            lm.create()
    else:
        lm.create()
        lm.run()
        lm.export()
        language_model.check_language_model(output_dir)
        assert_no_expr_in_log(flog, 'error')
