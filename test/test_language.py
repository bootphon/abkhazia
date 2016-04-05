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
"""Test of the 'abkhazia language' command"""

import os
import pytest
import tempfile
# import shutil

from abkhazia.kaldi.language_model import LanguageModel
# from abkhazia.prepare.buckeye_preparator import BuckeyePreparator
# import abkhazia.utils.split as split
import abkhazia.utils as utils

HERE = os.path.abspath(os.path.dirname(__file__))
levels = ['phone', 'word']
orders = [1, 2, 3, 4]
params = [(l, o) for l in levels for o in orders]


# def setup():
#     """Prepare 1% of buckeye in the data directory (random by utterances)"""
#     data_dir = os.path.join(HERE, 'data')
#     if not os.path.isdir(data_dir):
#         try:
#             # fail if buckeye not defined in abkhazia.cfg
#             raw_buckeye = BuckeyePreparator.default_input_dir()
#             if raw_buckeye is None:
#                 raise RuntimeError(
#                     'buckeye-directory not defined in abkhazia.cfg')

#             # prepare the buckeye corpus in default abkhazia dir
#             prep = BuckeyePreparator(raw_buckeye, njobs=4)
#             prep.prepare()  # we skip validation

#             # split 1% of buckeye by utterances
#             temp = tempfile.mkdtemp()
#             spliter = split.SplitCorpus(
#                 prep.output_dir, output_dir=temp)
#             spliter.split(train_prop=0.01)

#             shutil.move(
#                 os.path.join(temp, 'split', 'train', 'data'),
#                 data_dir)
#         finally:
#             utils.remove(temp)


# def teardown():
#     utils.remove(os.path.join(HERE, 'data'))


@pytest.mark.parametrize("level, order", params)
def test_lm(level, order):
    data_dir = HERE
    assert os.path.isdir(data_dir)

    output_dir = tempfile.mkdtemp()
    # output_dir = os.path.join(HERE, 'lm', '{}_{}'.format(level, order))
    try:
        utils.remove(output_dir)
    except OSError:
        pass

    lm = LanguageModel(data_dir, output_dir)
    lm.level = level
    lm.order = order
    lm.create()
    lm.run()
    lm.export()

    log = os.path.join(output_dir, 'logs', 'language.log')
    error_lines = []
    for line in open(log, 'r').readlines():
        if 'ERROR' in line:
            error_lines.append(line)
    print error_lines
    assert len(error_lines) == 0
