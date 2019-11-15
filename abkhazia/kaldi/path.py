# Copyright 2016, 2017 Thomas Schatz, Xuan-Nga Cao, Mathieu Bernard
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
"""Python implementation of the share/path.sh Kaldi script"""

import os
from abkhazia.utils import config


def kaldi_path():
    """Return an environment for running the abkhazia recipes"""
    env = os.environ

    env['LC_ALL'] = 'C'  # for expected sorting and joining behaviour

    kaldiroot = config.get('kaldi', 'kaldi-directory')
    kaldisrc = os.path.join(kaldiroot, 'src')

    targets = ('bin', 'featbin', 'fgmmbin', 'fstbin', 'gmmbin',
               'latbin', 'nnetbin', 'nnet2bin', 'sgmmbin', 'lmbin',
               'kwsbin', 'ivectorbin', 'online2bin', 'sgmm2bin')
    kaldibin = ':'.join((os.path.join(kaldisrc, target)
                        for target in targets))

    fstbin = os.path.join(kaldiroot, 'tools', 'openfst', 'bin')

    platform = 'macosx' if os.uname()[0] == 'Darwin' else 'i686-m64'
    lmbin = ':'.join([
        os.path.join(kaldiroot, 'tools', 'irstlm', 'bin'),
        os.path.join(kaldiroot, 'tools', 'srilm', 'bin'),
        os.path.join(kaldiroot, 'tools', 'srilm', 'bin', platform),
        os.path.join(kaldiroot, 'tools', 'sctk', 'bin')])

    if 'PATH' not in env:
        # PATH isn't in the environment, should not occur
        env['PATH'] = ':'.join([kaldibin, fstbin, lmbin])
    else:
        path = ':'.join([kaldibin, fstbin, lmbin])
        if path not in env['PATH']:
            env['PATH'] += ':' + path

    env['IRSTLM'] = os.path.join(kaldiroot, 'tools', 'irstlm')

    # was a bug -> error while loading shared libraries: libfstscript.so.1
    fstlib = os.path.join(kaldiroot, 'tools', 'openfst', 'lib')
    libfstscript = os.path.join(fstlib, 'libfstscript.so.1')
    assert os.path.exists(libfstscript)

    if 'LD_LIBRARY_PATH' not in env:
        env['LD_LIBRARY_PATH'] = fstlib
    else:
        if fstlib not in env['LD_LIBRARY_PATH']:
            env['LD_LIBRARY_PATH'] += ':' + fstlib

    return env
