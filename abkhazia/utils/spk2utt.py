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
"""A Python wrapper to the kaldi script"""

import os
import subprocess

import config


def spk2utt(utt2spk, spk2utt):
    """Create speaker to utterances file

    Create the spk2utt file with the list of all speakers
    mapped to the list of their utterances. Built from utt2spk

    """
    # path to the conversion perl script
    script = os.path.join(
        config.config.get('kaldi', 'kaldi-directory'),
        'egs/wsj/s5/utils/utt2spk_to_spk2utt.pl')

    try:
        # run the script, write self.speaker_file_rev
        subprocess.Popen(
            [script, utt2spk],
            stdout=open(spk2utt, 'w'),
            stderr=open(os.devnull)).wait()
    except OSError:
        raise OSError('kaldi script not found {}'.format(script))
