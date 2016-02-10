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
"""Provides functions to convert various audio formats to wav"""

import os
import shlex
import subprocess

from abkhazia.utils.config import get_config

def flac2wav(flac, wav):
    """Convert a flac file to the wav format

    'flac' must be an existing flac file
    'wav' is the filename of the created file

    This method lies on the 'flac --decode' system command. Raises an
    OSError if the command 'flac' is not found on the system.

    """
    try:
        subprocess.check_output(shlex.split('which flac'))
    except:
        raise OSError('flac is not installed on your system')

    command = 'flac --decode -s -f {} -o {}'.format(flac, wav)
    subprocess.call(shlex.split(command))


def sph2wav(sph, wav):
    """Convert a sph file to the wav format

    'sph' must be an existing sph file
    'wav' if the filename of the created file

    sph2pipe is required for converting sph to wav. This function look
    at it in the kaldi-directory entry in the abkahzia configuration
    file.

    """
    sph2pipe = os.path.join(get_config().get('kaldi', 'kaldi-directory'),
                            'tools/sph2pipe_v2.5/sph2pipe')
    if not os.path.isfile(sph2pipe):
        raise OSError('sph2pipe not found on your system')

    command = sph2pipe + ' -f wav {0} {1}'.format(sph, wav)
    subprocess.call(shlex.split(command))


def shn2wav(shn, wav):
    """Convert a shn file to the wav format

    'shn' must be an existing sph file
    'wav' if the filename of the created file

    sox and shorten commands are required

    shorten is available at
    http://etree.org/shnutils/shorten/dist/src/shorten-3.6.1.tar.gz

    sox is available at http://sox.sourceforge.net/ or in repositories
    of most Linux distribution (sudo apt-get install sox)

    """
    for cmd in ['shorten', 'sox']:
        try:
            subprocess.check_output(shlex.split('which {}'.format(cmd)))
        except:
            raise OSError('{} is not installed on your system'.format(cmd))

    tmp = shn + '.tmp'
    command1 = 'shorten -x {} {}'.format(shn, tmp)
    command2 = ('sox -t raw -r 16000 -e signed-integer -b 16 {} -t wav {}'
                .format(tmp, wav))

    for cmd in [command1, command2]:
        subprocess.call(shlex.split(cmd))

    try:
        os.remove(tmp)
    except os.error:
        pass
