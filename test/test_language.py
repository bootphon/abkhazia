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
import shlex
import subprocess
import tempfile

import abkhazia.utils as utils

HERE = os.path.abspath(os.path.dirname(__file__))


class TestWordBigram(object):
    def _run(self, level, order):
        cmd = ('abkhazia language {} -f --model-order {} --model-level {}'
               .format(self.data_dir, str(order), level))
        ps = subprocess.Popen(shlex.split(cmd), stdout=open(os.devnull))
        ps.wait()
        assert ps.returncode == 0

    def setup(self):
        self.data_dir = HERE
        self.output_dir = os.path.join(HERE, 'language')  # tempfile.mkdtemp()
        self._run('word', 2)
        self.root = os.path.join(self.output_dir, 'language', 's5')

    def teardown(self):
        # utils.remove(self.output_dir)
        pass

    def test_output_dirs(self):
        assert os.path.isdir(self.root)

    def test_log_errors(self):
        """Look for error in log files"""
        log1 = os.path.join(self.output_dir, 'logs', 'language.log')
        for line in open(log1, 'r').readlines():
            assert 'ERROR' not in line

        log2 = os.path.join(self.root, 'data', 'prepare_language.log')
        for line in open(log2, 'r').readlines():
            assert 'ERROR' not in line
