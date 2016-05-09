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
"""Provides some misc functions usefull to abkhazia"""

import codecs
import collections
import multiprocessing
import os
import re
import shutil

import config  # this is abkhazia.utils.config


def default_njobs(nj_queue=20):
    """Return `nj_queue` if running on a queue, ncores if running locally

    Default for `nj_queue` is 20, the standard number of jobs for
    features computation in the kaldi WSJ recipe.

    """
    cmd = config.config.get('kaldi', 'train-cmd')
    return nj_queue if 'queue' in cmd else multiprocessing.cpu_count()


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
    if s is True:
        return 'true'
    return 'false'


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


def list_directory(directory, abspath=False):
    """Return os.listdir(directory) with .DS_Store filtered out"""
    lsd = [e for e in os.listdir(directory) if e != '.DS_Store']
    if abspath:
        lsd = [os.path.abspath(os.path.join(directory, e)) for e in lsd]
    return lsd


def list_files_with_extension(directory, extension, abspath=False):
    """Return all files of given extension in directory hierarchy

    The files are returned in a list with a path relative to
    'directory' except if abspath is True

    """
    # the regular expression to match in filenames
    expr = r'(.*)' + extension + '$'

    # build the list of matching files
    matched = []
    for path, _, files in os.walk(directory):
        matched += [os.path.join(path, f) for f in files if re.match(expr, f)]
    if abspath:
        matched = [os.path.abspath(m) for m in matched]
    return matched


def remove(path, safe=False):
    """Remove a file, link or directory, raise OSError on failure

    If safe is True, don't raise on unexisting path

    """
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            # works for both files and links
            os.remove(path)
    except (shutil.Error, os.error) as err:
        if not safe:
            raise OSError(err)
        else:
            pass


def is_empty_file(path):
    """Return True if the file `path` is empty"""
    return os.stat(path).st_size == 0


def check_directory(dir, files, name='directory'):
    """Raise OSError any of the `files` is not present in `dir`"""
    if not os.path.isdir(dir):
        raise OSError('{} not found: {}.\n'.format(name, dir))

    for f in files:
        if not os.path.isfile(os.path.join(dir, f)):
            raise OSError(
                'non valid {}: {} not found in {}'.format(name, f, dir))
