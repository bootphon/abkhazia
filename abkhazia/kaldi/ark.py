# Copyright 2016 Thomas Schatz, Mathieu Bernard, Roland Thiolliere
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
"""Kaldi ark files input/output

Read/write ark files into numpy arrays, conversion to h5features file.

Provides the ark_to_dict and ark_to_h5f functions to convert Kaldi ark
files to Python dictionaries and h5features files
respectively. Provides the dict_to_ark function to write ark files
from numpy arrays.

"""

import os
import struct
import tempfile

import numpy as np
import h5features as h5f
import h5py

import abkhazia.utils as utils
from abkhazia.kaldi import kaldi_path


def ark_to_dict(arkfile):
    """Kaldi archive (ark) to dictionary of numpy arrays (~npz)

    Parameters:
    -----------

    arkfile (str): path to a Kaldi ark file, either in binary or text
        format.

    Return:
    -------

    A dictionary where keys are utterances ids (as str) and values are
    features matrices (as 2D numpy arrays).

    """
    if not _is_binary(arkfile):
        return _ark_to_dict_text(arkfile)

    try:
        return _ark_to_dict_binary(arkfile)
    except AssertionError:  # binary read failed
        return _ark_to_dict_binary_bytext(arkfile)


def ark_to_h5f(ark_files, h5_file, h5_group='features'):
    """Convert a sequence of kaldi ark files into a single h5feature file

    Parameters:
    -----------

    ark_files (sequence of str): a sequence of ark files to be
        converted into a single h5features file

    h5_file (str): the h5features file to write in

    h5_group (str): the group to write in the file, must not exist,
        default is 'features'

    Raise:
    ------

    AssertionError if the `h5_group` already exists in the `h5_file`

    """
    assert h5_group not in h5py.File(h5_file), \
        'group {} already exists in {}'.format(h5_group, h5_file)

    with h5f.Writer(h5_file) as fout:
        for ark in ark_files:
            fout.write(_ark_to_data(ark), h5_group, append=True)


def dict_to_ark(arkfile, data, format='text'):
    """Write a data dictionary to a Kaldi ark file

    Parameters:
    -----------

    arkfile (str): path to the ark file to write

    data (dict): dictionary of numpy arrays to write

    format (str): must be 'text' or 'binary' to write a text or a
        binary ark file respectively, default is 'text'

    Raise:
    ------

    RuntimeError if format is not 'text' or 'binary'

    """
    if format is 'text':
        _dict_to_txt_ark(arkfile, data)
    elif format is 'binary':
        with tempfile.NamedTemporaryFile() as tmp:
            _dict_to_txt_ark(tmp.name, data)

            utils.jobs.run(
                'copy-feats ark,t:{0} ark:{1}'.format(tmp.name, arkfile),
                env=kaldi_path(),
                stdout=open(os.devnull, 'w').write)
    else:
        raise RuntimeError(
            'ark format must be "text" or "binary", it is "{}"'
            .format(format))


#
# Functions above should be considered private
#


def _is_binary(arkfile):
    """Return True if the ark in binary, False if text"""
    # from https://stackoverflow.com/questions/898669
    textchars = bytearray(
        {7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
    return bool(open(arkfile, 'rb').read(1024).translate(None, textchars))


def _ark_to_data(arkfile, sample_frequency=100, tstart=0.0125):
    """Kaldi archive (ark) to h5features.Data

    Because Kaldi ark does not store time information, we need extra
    parameters for specifiying the time labels in the h5features file.

    Parameters:
    -----------

    arkfile (str) : Kaldi ark file to read from, can be text or binary

    sample_frequency (float): sampling rate of the features vectors

    tstart (float): timestamp of the first feature vector

    """
    d = ark_to_dict(arkfile)

    items = d.keys()
    features = d.values()
    times = map(
        lambda d: np.arange(d.shape[0], dtype=float) / sample_frequency +
        tstart, d.values())

    return h5f.Data(items, times, features)


def _ark_to_dict_binary(arkfile):
    res = {}
    with open(arkfile) as fin:
        while True:
            # TODO break if empty buffer here
            fname = ''
            c = fin.read(1)
            if c == '':  # EOF (EOFError not raised by read(empty))
                break
            while c != ' ':
                fname += c
                c = fin.read(1)

            # end of fname
            fin.read(1)

            # data type
            assert fin.read(4) == 'BFM ', 'type not supported'

            # nrows type
            assert struct.unpack('b', fin.read(1))[0] == 4, \
                'type not supported'
            nrows = struct.unpack('i', fin.read(4))[0]

            # ncols type:
            assert struct.unpack('b', fin.read(1))[0] == 4, \
                'type not supported'
            ncols = struct.unpack('i', fin.read(4))[0]

            # data
            size = nrows * ncols * 4
            data = np.fromstring(
                fin.read(size), dtype=np.float32).reshape((nrows, ncols))
            res[fname] = data
    return res


def _ark_to_dict_binary_bytext(arkfile):
    try:
        # copy-feats converts binary ark to text ark
        tempdir = tempfile.mkdtemp()
        txtfile = os.path.join(tempdir, 'txt')
        utils.jobs.run(
            'copy-feats ark:{0} ark,t:{1}'.format(arkfile, txtfile),
            env=kaldi_path(), stdout=open(os.devnull, 'w').write)

        # load the converted text ark as a dict
        return _ark_to_dict_text(txtfile)
    finally:
        utils.remove(tempdir, safe=True)


def _ark_to_dict_text(arkfile):
    res = {}
    tmparr = []
    utt_id = ''
    for line in open(arkfile, 'r'):
        splitted = line.strip().split()
        if splitted[-1] == '[':
            if utt_id:
                res[utt_id] = np.array(tmparr)
                tmparr = []
            utt_id = splitted[0]
        else:
            if splitted[-1] == ']':
                splitted = splitted[:-1]
            tmparr.append(map(float, splitted))
        res[utt_id] = np.array(tmparr)
    return res


def _dict_to_txt_ark(arkfile, data, sort=True):
    """Save `data` as a Kaldi ark `arkfile`"""
    with open(arkfile, 'w') as fark:
        for utt in sorted(data.iterkeys()) if sort else data.iterkeys():
            fark.write(utt + '  [\n')
            for vec in data[utt][:-1]:
                fark.write('  ' + ' '.join(str(v) for v in vec) + ' \n')
            fark.write('  ' + ' '.join(str(v) for v in data[utt][-1]) + ' ]\n')
