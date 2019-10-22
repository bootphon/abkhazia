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
"""Test of the abkhazia.models.features module"""

import h5features
import os
import pytest

import abkhazia.features as features
import abkhazia.utils as utils
import abkhazia.kaldi.ark as ark
from .conftest import assert_no_expr_in_log

params = [(pitch, ftype)
          for pitch in [True, False]
          for ftype in ['mfcc', 'fbank', 'plp']]


@pytest.mark.parametrize('pitch, ftype', params)
def test_features(pitch, ftype, corpus, tmpdir):
    output_dir = str(tmpdir.mkdir('feats'))
    flog = os.path.join(output_dir, 'feats.log')
    log = utils.logger.get_log(flog)

    # keep only 3 utterances for testing speed
    subcorpus = corpus.subcorpus(corpus.utts()[0:3])
    assert len(subcorpus.utts()) == 3

    # mfcc with few channels
    nbc = 3
    feat = features.Features(subcorpus, output_dir, log=log)
    feat.type = ftype
    feat.njobs = 1
    feat.use_pitch = pitch
    feat.delete_recipe = False
    feat.features_options.append(
        ('num-ceps' if ftype in ('mfcc', 'plp') else 'num-mel-bins', nbc))

    try:
        feat.compute()
    except RuntimeError as err:
        import sys
        sys.stdout.write(open(flog, 'r').read())
        sys.stdout.write(open(
            os.path.join(
                output_dir, 'recipe',
                'exp/make_mfcc/features/make_mfcc_pitch_features.1.log'),
            'r').read())
        sys.stdout.write(open(
            os.path.join(
                output_dir, 'recipe/conf/mfcc.conf'), 'r').read())
        raise err


    # # actually ERROR is in the vocabulary so this test fails...
    # assert_no_expr_in_log(flog, 'error')

    # basic asserts on files
    assert os.path.isfile(os.path.join(output_dir, 'meta.txt'))
    features.Features.check_features(output_dir)

    # convert to h5features and read it back
    h5 = os.path.join(output_dir, 'feats.h5')
    ark.scp_to_h5f(os.path.join(output_dir, 'feats.scp'), h5)
    data = h5features.Reader(h5, 'features').read()

    # check we have nbc or nbc+3 channels
    dim = data.features()[0].shape[1]
    exp = nbc + 3 if pitch else nbc
    assert dim == exp, 'bad dim: {}, expected {}'.format(dim, exp)

    # check utt_ids in h5f are consistent with corpus
    times = data.dict_labels()
    assert len(times.keys()) == len(subcorpus.utts())
    for t, c in zip(times.keys(), subcorpus.utts()):
        assert t == c
