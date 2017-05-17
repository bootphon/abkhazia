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
"""Test of the abkhazia.decode module"""

import os

import abkhazia.decode as decode
import abkhazia.utils as utils
from .conftest import assert_no_expr_in_log


def test_decode_mono(corpus, lm_word, features, am_mono, tmpdir):
    output_dir = str(tmpdir.mkdir('decode-mono'))
    flog = os.path.join(output_dir, 'decode-mono.log')
    log = utils.logger.get_log(flog)

    decoder = decode.Decode(
        corpus, lm_word, features, am_mono, output_dir, log=log)
    decoder.decode_opts['max-active'].value = 70
    decoder.decode_opts['beam'].value = 3
    decoder.decode_opts['lattice-beam'].value = 2
    decoder.compute()

    # check if we have no error and a WER file
    assert_no_expr_in_log(flog, 'error')
    assert os.path.isfile(
        os.path.join(output_dir, 'scoring_kaldi', 'best_wer'))


def test_decode_tri(corpus, lm_word, features, am_tri, tmpdir):
    output_dir = str(tmpdir.mkdir('decode-tri'))
    flog = os.path.join(output_dir, 'decode-tri.log')
    log = utils.logger.get_log(flog)

    decoder = decode.Decode(
        corpus, lm_word, features, am_tri, output_dir, log=log)
    decoder.decode_opts['max-active'].value = 15
    decoder.decode_opts['beam'].value = 2
    decoder.decode_opts['lattice-beam'].value = 1
    decoder.compute()

    # check if we have no error and a WER file
    assert_no_expr_in_log(flog, 'error')
    assert os.path.isfile(
        os.path.join(output_dir, 'scoring_kaldi', 'best_wer'))


def test_decode_trisa(corpus, lm_word, features, am_trisa, tmpdir):
    output_dir = str(tmpdir.mkdir('decode-trisa'))
    flog = os.path.join(output_dir, 'decode-trisa.log')
    log = utils.logger.get_log(flog)

    decoder = decode.Decode(
        corpus, lm_word, features, am_trisa, output_dir, log=log)
    decoder.decode_opts['max-active'].value = 15
    decoder.decode_opts['beam'].value = 2
    decoder.decode_opts['first-max-active'].value = 10
    decoder.decode_opts['first-beam'].value = 1
    decoder.decode_opts['lattice-beam'].value = 1
    decoder.compute()

    # check if we have no error and a WER file
    assert_no_expr_in_log(flog, 'error')
    assert os.path.isfile(
        os.path.join(output_dir, 'scoring_kaldi', 'best_wer'))


def test_decode_nnet(corpus, lm_word, features, am_nnet, tmpdir):
    output_dir = str(tmpdir.mkdir('decode-nnet'))
    flog = os.path.join(output_dir, 'decode-nnet.log')
    log = utils.logger.get_log(flog)

    decoder = decode.Decode(
        corpus, lm_word, features, am_nnet, output_dir, log=log)
    decoder.decode_opts['beam'].value = 2
    decoder.decode_opts['min-active'].value = 2
    decoder.decode_opts['max-active'].value = 70
    decoder.decode_opts['lattice-beam'].value = 1
    decoder.compute()

    # check if we have no error and a WER file
    assert_no_expr_in_log(flog, 'error')
    assert os.path.isfile(
        os.path.join(output_dir, 'scoring_kaldi', 'best_wer'))
