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
"""Wrapper for getting/setting optional parameters of a Kaldi executable"""

import re
import shlex
import subprocess

from abkhazia.kaldi.path import kaldi_path


class OptionEntry(object):
    """Entry read from / send to a Kaldi executable"""
    def __init__(self, help='', type=None, default=None, value=None):
        self.help = help
        self.type = type
        self.default = default
        self.value = value


def get_options(executable):
    """Return the options taken by `executable` as a dictionary of entries"""
    try:
        # help message displayed on stderr with --help argument
        helpmsg = subprocess.Popen(
            shlex.split(executable + ' --help'),
            stderr=subprocess.PIPE,
            env=kaldi_path()).communicate()[1]
    except OSError:
        raise RuntimeError('No such executable "{}"'.format(executable))

    # parse the help to extract only the options paragraph
    lbegin = 0
    lend = 0
    for n, line in enumerate(helpmsg.split('\n')):
        if lbegin == 0 and line.startswith('Options:'):
            lbegin = n+1
        if lbegin != 0 and line.startswith('Standard options:'):
            lend = n-1
            break
    raw_options = (o.strip() for o in helpmsg.split('\n')[lbegin:lend])

    # parse each option line as an OptionEntry instance in a list
    options = {}
    for opt in raw_options:
        matched = re.match(
            '^--([a-zA-Z-0-9\-]+)\s+: (.*)\((.*), default = (.*)\)$', opt)
        options[matched.group(1)] = OptionEntry(
            help=matched.group(2).strip(),
            type=matched.group(3),
            default=matched.group(4),
            value=None)
    return options
