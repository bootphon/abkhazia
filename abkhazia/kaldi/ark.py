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

Read/write ark files into numpy arrays or h5features file.

Provides the ark_to_dict, ark_to_h5f and scp_to_h5f functions to
convert Kaldi ark files to Python dictionaries and h5features files
respectively.

Provides the dict_to_ark function to write ark files from numpy
arrays.

"""

import os
import re
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
    except AssertionError:
        return _ark_to_dict_binary_bytext(arkfile)


def ark_to_h5f(ark_files, h5_file, h5_group='features',
               sample_frequency=100, tstart=0.0125,
               log=utils.logger.null_logger()):
    """Convert a sequence of kaldi ark files into a single h5features file

    Because Kaldi ark does not store any time information, we need
    extra parameters for specifiying the time labels in the h5features
    file.

    Parameters:
    -----------

    ark_files (sequence of str): a sequence of ark files to be
        converted into a single h5features file

    h5_file (str): the h5features file to write in

    h5_group (str): the group to write in the file, must not exist,
        default is 'features'

    sample_frequency (float): sampling rate of the features vectors

    tstart (float): timestamp of the first feature vector

    log (logging.Logger): optional log for messages

    Raise:
    ------

    AssertionError if the `h5_group` already exists in the `h5_file`

    """
    ark_files = list(ark_files)

    if os.path.isfile(h5_file):
        assert h5_group not in h5py.File(h5_file, 'r'), \
            'group {} already exists in {}'.format(h5_group, h5_file)

    log.debug('converting %s ark file%s to h5features in %s/%s',
              len(ark_files),
              's' if len(ark_files) else '',
              h5_file, h5_group)

    with h5f.Writer(h5_file) as fout:
        for ark in ark_files:
            log.debug('converting {}...'.format(os.path.basename(ark)))
            fout.write(_ark_to_data(
                ark, sample_frequency=sample_frequency, tstart=tstart),
                       h5_group, append=True)


def scp_to_h5f(scp_file, h5_file, h5_group='features',
               sample_frequency=100, tstart=0.0125,
               log=utils.logger.null_logger()):
    """Convert ark files referenced in `scp_file` into a h5features file

    Because Kaldi ark does not store any time information, we need
    extra parameters for specifiying the time labels in the h5features
    file.

    Parameters:
    -----------

    scp_file (str): a scp file to be converted into a single
        h5features file

    h5_file (str): the h5features file to write in

    h5_group (str): the group to write in the file, must not exist,
        default is 'features'

    sample_frequency (float): sampling rate of the features vectors

    tstart (float): timestamp of the first feature vector

    log (logging.Logger): optional log for messages

    Raise:
    ------

    AssertionError if the `h5_group` already exists in the `h5_file`

    IOError if the scp file is badly formatted

    """
    # extract the ark files referenced in the scp
    ark_files = set()
    for n, line in enumerate(open(scp_file, 'r').readlines(), 1):
        matched = re.match('^.* (.*):[0-9]*$', line)
        if not matched:
            raise IOError('Bad scp file line {}: {}'.format(n, scp_file))
        ark_files.add(matched.group(1))

    # sort them in natural order to have f.10.ark > f.9.ark. This is
    # important to concatenate features in order because some Kaldi
    # scripts assumes ordered features (with the rspecifier ark,s,cs).
    ark_files = list(ark_files)
    ark_files.sort(key=utils.natural_sort_keys)

    log.info('writing {} ark files to {} in group {}'.format(
        len(ark_files), os.path.basename(h5_file), h5_group))

    # Then deleguate to ark_to_h5f
    ark_to_h5f(ark_files, h5_file, h5_group,
               sample_frequency=sample_frequency, tstart=tstart,
               log=log)


def dict_to_ark(arkfile, data, format='text'):
    """Write a data dictionary to a Kaldi ark file

    TODO for now time information from h5f is lost in ark

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
        with tempfile.NamedTemporaryFile(
                dir=utils.config.get('abkhazia', 'tmp-directory')) as tmp:
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


def _ark_to_data(arkfile, sample_frequency=100, tstart=0.0125):
    """ark to h5features.Data"""
    d = ark_to_dict(arkfile)

    times = [np.arange(val.shape[0], dtype=float) / sample_frequency + tstart
             for val in d.values()]

    return h5f.Data(list(d.keys()), times, list(d.values()))


def _is_binary(arkfile):
    """Return True if the ark is binary, False if text"""
    # from https://stackoverflow.com/questions/898669
    textchars = bytearray(
        {7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
    return bool(open(arkfile, 'rb').read(1024).translate(None, textchars))


def _ark_to_dict_binary(arkfile):
    res = {}
    with open(arkfile, 'rb') as fin:
        while True:
            # TODO break if empty buffer here
            fname = b''
            c = fin.read(1)
            if c == b'':  # EOF (EOFError not raised by read(empty))
                break
            while c != b' ':
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
            data = np.frombuffer(
                fin.read(size), dtype=np.float32).reshape((nrows, ncols))
            res[fname.decode()] = data
    return res


def _ark_to_dict_binary_bytext(arkfile):
    """Convert a binary ark to text, and load it as numpy arrays"""
    try:
        # copy-feats converts binary ark to text ark
        tempdir = tempfile.mkdtemp(
            dir=utils.config.get('abkhazia', 'tmp-directory'))
        txtfile = os.path.join(tempdir, 'txt')
        utils.jobs.run(
            'copy-feats ark:{0} ark,t:{1}'.format(arkfile, txtfile),
            env=kaldi_path(), stdout=open(os.devnull, 'w').write)

        # load the converted text ark as a dict
        return _ark_to_dict_text(txtfile)
    finally:
        utils.remove(tempdir, safe=True)


def _ark_to_dict_text(arkfile):
    """Load a text ark to utterances indexed numpy arrays"""
    return {utt: data for utt, data in _yield_utt(arkfile)}


def _str2np(data):
    """Convert a list of str to a np.array of float"""
    npdata = np.zeros((len(data), len(data[0].split())))
    for i, line in enumerate(data):
        try:
            npdata[i, :] = [float(f) for f in line.split()]
        except ValueError:
            raise ValueError(
                'error converting str to float in:', line.strip())
    return npdata


def _yield_utt(arkfile):
    """Yield (utt_id, data) tuples read from a text `arkfile`"""
    utt_id = None
    data = []

    for line in open(arkfile, 'r'):
        # a new utterance is starting, yield the previous utt if any
        if not line.startswith('  '):
            if utt_id:
                yield utt_id, _str2np(data)
                utt_id, data = None, []
            utt_id = line[:-2].strip()
        else:  # line of floats
            data.append(line.replace(']', '').strip())

    # yield the final utt
    if utt_id:
        yield utt_id, _str2np(data)


def _dict_to_txt_ark(arkfile, data, sort=True):
    """Save `data` as a Kaldi ark `arkfile`"""
    with open(arkfile, 'w') as fark:
        for utt in sorted(data.keys()) if sort else data.keys():
            fark.write(utt + '  [\n')
            for vec in data[utt][:-1]:
                fark.write('  ' + ' '.join(str(v) for v in vec) + ' \n')
            fark.write('  ' + ' '.join(str(v) for v in data[utt][-1]) + ' ]\n')
