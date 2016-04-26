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
"""Provides some functions to work on cha files"""

import pkg_resources
import re
import subprocess
import tempfile

import utils  # this is abkhazia.utils


def nadults(cha):
    """Return the number of adult speakers recorded in `cha`"""
    # speaker IDs, lines starting with '@ID', forced to lowercase
    spks = (l.strip().lower() for l in utils.open_utf8(cha, 'r')
            if l.startswith('@ID'))

    # exclude non-adult speakers
    exclude = ['sibl', 'broth', 'sist', 'target', 'child', 'to',
               'environ', 'cousin', 'non_hum', 'play']

    # count non-excluded speakers
    return sum(all(e not in spk for e in exclude) for spk in spks)


def audio(cha):
    """Return the first audio media attached to the `cha` file

    Raise IOError if no audio media found.

    """
    for line in open(cha, 'r'):
        match = re.match('@Media:.+, audio', line)
        if match:
            return match.group(0).replace(
                ', audio', '').replace('@Media:', '').strip()
    raise IOError('no audio media found in {}'.format(cha))


def clean(lines):
    """Return a list of cleaned utterances from a set of raw cha lines

    This function is a wrapper on the share/cha_cleanup.sh script, see
    there for more details...

    """
    script = pkg_resources.resource_filename(
        pkg_resources.Requirement.parse('abkhazia'),
        'abkhazia/share/cha_cleanup.sh')

    with tempfile.TemporaryFile('w+') as tmpout:
        with tempfile.TemporaryFile('w+') as tmpin:
            tmpin.write('\n'.join(lines).encode('utf-8'))
            tmpin.seek(0)
            subprocess.call([script], stdin=tmpin, stdout=tmpout)
        tmpout.seek(0)
        return [l.strip() for l in tmpout.readlines()]
