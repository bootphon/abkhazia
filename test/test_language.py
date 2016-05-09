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

from abkhazia.core.language_model import LanguageModel, word2phone
import abkhazia.utils as utils

HERE = os.path.abspath(os.path.dirname(__file__))
levels = ['phone', 'word']
orders = [1, 2, 3]
params = [(l, o) for l in levels for o in orders]


class TestLanguage(object):
    def setup(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.tmp_dir, 'lang')
        self.data_dir = HERE
        self.lm = LanguageModel(self.data_dir, self.output_dir, verbose=True)

    def teardown(self):
        utils.remove(self.tmp_dir, safe=True)
        del self.lm

    def test_word2phone(self):
        root = os.path.join(self.data_dir, 'data')
        lexicon = os.path.join(root, 'lexicon.txt')
        text = os.path.join(root, 'text.txt')
        out = os.path.join(self.tmp_dir, 'w2p')
        word2phone(lexicon, text, out)

        assert len(utils.open_utf8(text, 'r').readlines()) == \
            len(utils.open_utf8(out, 'r').readlines())

    def test_recipe(self):
        lm = self.lm
        lm.level = 'phone'
        lm.order = 1
        lm.delete_recipe = False
        lm.create()
        lm.run()
        lm.export()

        recipe = os.path.join(self.output_dir, 'recipe')
        assert os.path.isdir(recipe)
        for f in ('steps', 'utils'):
            assert os.path.islink(os.path.join(recipe, f))
            assert os.path.isdir(os.path.join(recipe, f))

    def test_no_recipe(self):
        lm = self.lm
        lm.level = 'phone'
        lm.order = 1
        lm.delete_recipe = True
        lm.create()
        lm.run()
        lm.export()

        recipe = os.path.join(self.output_dir, 'recipe')
        assert not os.path.isdir(recipe)

    @pytest.mark.parametrize("level, order", params)
    def test_lm(self, level, order):
        lm = self.lm
        lm.level = level
        lm.order = order
        lm.create()
        lm.run()
        lm.export()

    #     # log = os.path.join(output_dir, 'language.log')
    #     # error_lines = []
    #     # for line in open(log, 'r').readlines():
    #     #     if 'ERROR' in line:
    #     #         error_lines.append(line)
    #     #     print error_lines
    #     # assert len(error_lines) == 0
