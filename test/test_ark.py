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
"""Test of the abkhazia.kaldi.io module"""

import os

import h5features as h5f
import numpy as np
import pytest

import abkhazia.kaldi.ark as io


@pytest.yield_fixture(scope='session')
def data(shape=(100, 5)):
    """Return a random numpy array given its shape"""
    yield {'test': np.random.random_sample(shape)}


@pytest.mark.parametrize('format', ['text', 'binary'])
def test_read_write(tmpdir, format, data):
    # write the array as an ark file and reload it
    ark = os.path.join(str(tmpdir), 'ark')
    io.dict_to_ark(ark, data, format=format)
    data2 = io.ark_to_dict(ark)

    assert data.keys() == data2.keys()
    assert np.allclose(data['test'], data2['test'], rtol=0, atol=1e-7)


@pytest.mark.parametrize('name', ['a', 'a-b', 'a_b'])
def test_h5f_name_of_utterance(tmpdir, data, name):
    data = {name: data['test']}

    ark = os.path.join(str(tmpdir), 'ark')
    io.dict_to_ark(ark, data)

    # convert it to h5features file
    h5file = os.path.join(str(tmpdir), 'h5f')
    io.ark_to_h5f([ark], h5file)

    data2 = h5f.Reader(h5file).read()
    assert np.allclose(data2.dict_features()[name], data[name])


def test_h5f_twice(tmpdir, data):
    # add a 2nd item in data
    data.update({'test2': data['test']})

    # write the array as an ark file
    ark = os.path.join(str(tmpdir), 'ark')
    ark2 = os.path.join(str(tmpdir), 'ark2')
    io.dict_to_ark(ark, data)
    io.dict_to_ark(ark2, {k+'_2': v for k, v in data.iteritems()})

    # convert it to h5features file
    h5file = os.path.join(str(tmpdir), 'h5f')
    io.ark_to_h5f([ark, ark2], h5file, 'test')

    # get back data from h5f
    data2 = h5f.Reader(h5file, 'test').read()
    print data2.items()
    assert data2.items() == ['test', 'test2', 'test2_2', 'test_2']
    assert data2.dict_labels()['test'].shape[0] == data['test'].shape[0]
    assert data['test'].shape == data2.dict_features()['test'].shape
    assert data['test'].shape == data2.dict_features()['test2_2'].shape
    assert np.allclose(data2.dict_features()['test'], data['test'])
    assert np.allclose(data2.dict_features()['test2_2'], data['test'])

    # test writing in an existing group
    with pytest.raises(AssertionError):
        io.ark_to_h5f([ark], h5file, 'test')
