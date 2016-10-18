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
"""Provides path/files related functions usefull to abkhazia"""

import os
import re
import shutil


def list_directory(directory, abspath=False):
    """Return os.listdir(directory) with .DS_Store filtered out"""
    lsd = [e for e in os.listdir(directory) if e != '.DS_Store']
    if abspath:
        lsd = [os.path.abspath(os.path.join(directory, e)) for e in lsd]
    return lsd


def list_files_with_extension(
        directory, extension,
        abspath=False, realpath=True, recursive=True):
    """Return all files of given extension in directory hierarchy

    The files are returned in a sorted list with a path relative to
    'directory', except if abspath or realpath is True

    If `abspath` is True, return absolute path to the file/link

    If `realpath` is True, return resolved links

    If `recursive` is True, list files in the whole subdirectories
        structure, if False just list the top-level directory

    """
    # the regular expression to match in filenames
    expr = r'(.*)' + extension + '$'

    # build the list of matching files
    matched = []
    if recursive:
        for path, _, files in os.walk(directory):
            matched += [os.path.join(path, f)
                        for f in files if re.match(expr, f)]
    else:
        matched = [os.path.join(directory, f)
                   for f in os.listdir(directory) if re.match(expr, f)]

    if abspath:
        matched = [os.path.abspath(m) for m in matched]
    if realpath:
        matched = [os.path.realpath(m) for m in matched]
    return sorted(matched)


def remove(path, safe=False):
    """Remove a file, link or directory, raise OSError on failure

    If safe is True, don't raise on unexisting path

    """
    try:
        if os.path.isdir(path) and not os.path.islink(path):
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


def symlink_files(files, destdir):
    """Create symlinks of the `files` in the directory `destdir`

    `destdir` is created if non-existing, any file in `files` already
    present in `destdir` is not linked.

    """
    if not os.path.isdir(destdir):
        os.mkdir(destdir)

    for src in files:
        dest = os.path.join(destdir, os.path.basename(src))
        if not os.path.isfile(dest):
            os.symlink(src, dest)
