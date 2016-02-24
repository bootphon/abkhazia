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

import audiotools
import collections
import joblib
import os
import shlex
import subprocess
import wave

from abkhazia.utils.config import get_config

def flac2wav(flac, wav):
    audiotools.open(flac).convert(wav, audiotools.WaveAudio)

# def shn2wav(shn, wav):
#     audiotools.open(shn).convert(wav, audiotools.WavAudio)

# def flac2wav(flac, wav):
#     """Convert a flac file to the wav format

#     'flac' must be an existing flac file
#     'wav' is the filename of the created file

#     This method lies on the 'flac --decode' system command. Raises an
#     OSError if the command 'flac' is not found on the system.

#     """
#     try:
#         subprocess.check_output(shlex.split('which flac'))
#     except:
#         raise OSError('flac is not installed on your system')

#     command = 'flac --decode -s -f {} -o {}'.format(flac, wav)
#     subprocess.call(shlex.split(command))


def sph2wav(sph, wav):
    """Convert a sph file to the wav format

    'sph' must be an existing sph file
    'wav' if the filename of the created file

    sph2pipe is required for converting sph to wav. This function look
    at it in the abkahzia configuration file.

    """
    sph2pipe = os.path.join(get_config().get('kaldi', 'kaldi-directory'),
                            'tools/sph2pipe_v2.5/sph2pipe')
    if not os.path.isfile(sph2pipe):
        raise OSError('sph2pipe not found on your system')

    command = sph2pipe + ' -f wav {} {}'.format(sph, wav)
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

    # TODO use mkstemp instead
    tmp = wav + '.tmp'
    command1 = 'shorten -x {} {}'.format(shn, tmp)
    command2 = ('sox -t raw -r 16000 -e signed-integer -b 16 {} -t wav {}'
                .format(tmp, wav))

    for cmd in [command1, command2]:
        subprocess.call(shlex.split(cmd))

    try:
        os.remove(tmp)
    except os.error:
        pass


def convert(inputs, outputs, fileformat, njobs=1, verbose=5):
    """Convert a range of audio files to the wav format

    inputs: list of input files to convert
    outputs: list of the converted wav files
    fileformat: audio format of the input files, must be in {flac, sph, shn}
    njobs: the number of parallel conversions

    We must have len(inputs) == len(wavs), all files in inputs must
    exist. For details on the verbose level, please refeer to the
    joblib documentation.

    """
    # mapping from file format to conversion function
    try:
        fnc = {
            'flac': flac2wav,
            'sph': sph2wav,
            'shn': shn2wav
        }[fileformat]
    except KeyError:
        raise IOError('{} is not a supported format'.format(fileformat))

    # assert inputs and outputs have the same size
    if not len(inputs) == len(outputs):
        raise IOError('inputs and outputs have a different size')

    # assert all input files exist
    for i in inputs:
        if not os.path.isfile(i):
            raise IOError('input file does not exist: {}'.format(i))

    # convert files in parallel
    joblib.Parallel(n_jobs=njobs, verbose=verbose)(
        joblib.delayed(fnc)(i, o) for i, o in zip(inputs, outputs))


_metawav = collections.namedtuple(
    '_metawav', 'nbc width rate nframes comptype compname duration')

def _scan_one(wav):
    """scan a single wav file and return a metawav tuple"""
    try:
        param = wave.open(wav, 'r').getparams()
        return _metawav(
            param[0], param[1], param[2],
            param[3], param[4], param[5],
            param[3]/float(param[2]))  # duration
    except EOFError:
        return _metawav(nframes=0)

def scan(wavs, njobs=1, verbose=5):
    """Return meta information on the input `wavs` files

    wavs : a list of absolute paths to wav files
    njobs : the number of parallel scans

    The returned dict 'metainfo' have wavs for keys and the following
    named tuple as value:

        metainfo[wav].{nbc width rate nframes comptype compname duration}

    For example access to the duration the 3rd wav in `wavs` with::

        metainfo = scan(wavs)
        d = metainfo[wavs[2]].duration

    See the documentation of wave.getparams() for details.

    """
    res = joblib.Parallel(n_jobs=njobs, verbose=verbose)(
        joblib.delayed(_scan_one)(wav) for wav in wavs)

    return dict(zip(wavs, res))
