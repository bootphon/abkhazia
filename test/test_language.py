# coding: utf-8

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

from abkhazia.models.language_model import (
    LanguageModel, word2phone, check_language_model)
import abkhazia.utils as utils

levels = ['phone', 'word']
orders = [1, 2, 3]
params = [(l, o) for l in levels for o in orders]


@pytest.mark.usefixtures('corpus')
class TestLanguage(object):
    def setup(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.tmp_dir, 'lang')
        self.flog = os.path.join(self.output_dir, 'language.log')

    def teardown(self):
        utils.remove(self.tmp_dir, safe=True)

    def test_word2phone(self, corpus):
        phones = word2phone(corpus)

        assert sorted(phones.keys()) == sorted(corpus.utts())
        assert len(phones) == len(corpus.text)

    @pytest.mark.parametrize("level, order", params)
    def test_lm(self, level, order, corpus):
        lm = LanguageModel(
            corpus, self.output_dir, log=utils.get_log(self.flog))

        lm.level = level
        lm.order = order
        lm.create()
        lm.run()
        lm.export()
        check_language_model(self.output_dir)

        assert os.path.isfile(self.flog)
        error_lines = []
        for line in open(self.flog, 'r').readlines():
            if 'error' in line.lower():
                error_lines.append(line)
            print error_lines
        assert len(error_lines) == 0
