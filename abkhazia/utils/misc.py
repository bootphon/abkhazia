# Copyright 2016 Thomas Schatz, Xuan-Nga Cao, Mathieu Bernard
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
"""Provides some misc functions usefull to abkhazia"""

import codecs
import collections
import multiprocessing
import re

import config  # this is abkhazia.utils.config


def default_njobs(nj_queue=20, local=False):
    """Return `nj_queue` if running on a queue, ncores if running locally

    Default for `nj_queue` is 20, the standard number of jobs for
    features computation in the kaldi WSJ recipe.

    """
    cmd = config.config.get('kaldi', 'train-cmd')
    return (nj_queue if not local and 'queue' in cmd
            else multiprocessing.cpu_count())


def str2bool(s, safe=False):
    """Return True if s=='true', False if s=='false'

    If s is already a bool return it, else raise TypeError.
    If `safe` is True, never raise but return False instead.

    """
    if isinstance(s, bool):
        return s

    if safe:
        return True if s == 'true' else False
    else:
        if s == 'true':
            return True
        if s == 'false':
            return False
    raise TypeError("{} must be 'true' or 'false'".format(s))


def bool2str(s):
    """Return 'true' if `s` is True, else return 'false'"""
    return 'true' if s else 'false'


# from https://stackoverflow.com/questions/38987
def merge_dicts(*dict_args):
    """Given any number of dicts, shallow copy and merge into a new dict

    Precedence goes to (key, value) pairs in latter dicts.

    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def duplicates(iterable):
    """Return a list of duplicated elements in an iterable"""
    counts = collections.Counter(iterable)
    return [e for e in counts if counts[e] > 1]


# From https://www.peterbe.com/plog/uniqifiers-benchmark
def unique(seq, sort=False):
    """Return a list of elements in `seq` with duplicates removed

    Do not preserve order of the sequence. If `sort` is True, return a
    sorted list.

    """
    keys = {}
    for e in seq:
        keys[e] = 1
    return sorted(keys.keys()) if sort else keys.keys()


def open_utf8(filename, mode='rb'):
    """Open a file encoded in UTF-8 and return its handler"""
    return codecs.open(filename, mode=mode, encoding='UTF-8')


def natural_sort_keys(text):
    """list.sort(key=natural_sort_keys) sorts in human order

    See https://stackoverflow.com/questions/5967500

    """
    def atoi(text):
        return int(text) if text.isdigit() else text
    return [atoi(c) for c in re.split('(\d+)', text)]
