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

from abkhazia.kaldi.language_model import LanguageModel
import abkhazia.utils as utils

HERE = os.path.abspath(os.path.dirname(__file__))
levels = ['phone', 'word']
orders = [1, 2, 3, 4]
params = [(l, o) for l in levels for o in orders]
# params = [('word', 3)]


@pytest.mark.parametrize("level, order", params)
def test_lm(level, order):
    data_dir = HERE
    assert os.path.isdir(data_dir)

    output_dir = tempfile.mkdtemp()
    try:
        lm = LanguageModel(data_dir, output_dir, verbose=True)
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
    finally:
        utils.remove(output_dir, safe=True)
