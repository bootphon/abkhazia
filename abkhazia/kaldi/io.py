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
"""Numpy / Kaldi ark files interface

This module is a 'best of' the feature_extraction bootphon package and
earlier versions of abkhazia.

"""

import os
import struct
import tempfile

import numpy as np
import h5features as h5f
import abkhazia.utils as utils
from abkhazia.kaldi import kaldi_path


def ark2dict(arkfile):
    """Kaldi archive (ark) to dictionnary of numpy arrays (~npz)

    ..note: Only standard features files supported, and float (no doubles)

    """
    try:
        res = {}
        with open(arkfile) as fin:
            while True:
                # TODO: break if empty buffer here
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
    except AssertionError:
        # binary read failed, convert binary to text and then read
        # from text
        return ark2dict_bytext(arkfile)


def ark2dict_bytext(arkfile):
    try:
        tempdir = tempfile.mkdtemp()
        txtfile = os.path.join(tempdir, 'txt')
        utils.jobs.run(
            'copy-feats ark:{0} ark,t:{1}'.format(arkfile, txtfile),
            env=kaldi_path(), stdout=open(os.devnull, 'w').write)
        return textark2dict(txtfile)
    finally:
        utils.remove(tempdir, safe=True)


def textark2dict(arkfile):
    res = {}
    tmparr = []
    arrname = ''
    for line in open(arkfile, 'r'):
        splitted = line.strip().split()
        if splitted[-1] == '[':
            # if arrname:
            #     res[arrname] = np.array(tmparr)
            arrname = splitted[0]
        else:
            # if splitted[-1] == ']':
            #     splitted = splitted[:-1]
            # tmparr.append(map(float, splitted))
            res[arrname] = ''  # np.array(tmparr)
    return res


def ark2data(arkfile):
    """Kaldi archive (ark) to h5features.Data"""
    d = ark2dict(arkfile)
    items = d.keys()
    features = d.values()
    times = map(lambda d: np.arange(d.shape[0], dtype=float) / 100 +
                0.0125, d.values())
    return h5f.Data(items, times, features)


def ark_to_h5f(ark_files, h5_file, h5_group='features'):
    """Convert a sequence of kaldi ark files into a single h5feature file"""
    with h5f.Writer(h5_file) as fout:
        for ark in ark_files:
            fout.write(ark2data(ark), h5_group, append=True)
