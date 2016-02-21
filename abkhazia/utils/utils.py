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
"""Provides some misc functions usefull to abkahzia"""

import codecs
import os
import re
import shutil


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


def remove(path):
    """Remove a file, link or directory, raise OSError on failure"""
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            # works for files and links
            os.remove(path)
    except (shutil.Error, os.error) as err:
        raise OSError(err)


def is_empty_file(path):
    """Return True if the file `path` is empty"""
    return os.stat(path).st_size == 0
