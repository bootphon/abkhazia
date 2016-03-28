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
# along with abkahzia. If not, see <http://www.gnu.org/licenses/>.
"""Python implementation of the share/path.sh"""

import os

import abkhazia.utils as utils


def kaldi_path():
    """Return an environment for running the abkhazia recipes"""
    env = {}
    env['kaldiroot'] = utils.config.get('kaldi', 'kaldi-directory')
    env['kaldisrc'] = os.path.join(env['kaldiroot'], 'src')

    targets = ('bin', 'featbin', 'fgmmbin', 'fstbin', 'gmmbin',
               'latbin', 'nnetbin', 'sgmmbin', 'lmbin', 'kwsbin', 'ivectorbin',
               'online2bin', 'sgmm2bin')
    kaldibin = ':'.join((os.path.join(env['kaldisrc'], target)
                        for target in targets))

    fstbin = os.path.join(env['kaldiroot'], 'tools', 'openfst', 'bin')
    lmbin = ':'.join([
        os.path.join(env['kaldiroot'], 'tools', 'irstlm', 'bin'),
        os.path.join(env['kaldiroot'], 'tools', 'srilm', 'bin'),
        os.path.join(env['kaldiroot'], 'tools', 'srilm', 'bin', 'i686-m64'),
        os.path.join(env['kaldiroot'], 'tools', 'sctk', 'bin')])

    try:
        env['PATH'] = ':'.join([os.environ['PATH'], kaldibin, fstbin, lmbin])
    except KeyError:
        env['PATH'] = ':'.join([kaldibin, fstbin, lmbin])

    env['LC_ALL'] = 'C'  # for expected sorting and joining behaviour
    env['IRSTLM'] = os.path.join(env['kaldiroot'], 'tools', 'irstlm')

    return utils.merge_dicts(os.environ, env)
