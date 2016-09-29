# coding: utf-8

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
"""Provides some functions to work on cha files

Cha format is used by some corpora abkhazia have preparators for. See
http://childes.psy.cmu.edu/manuals/CHAT.pdf for detailed info on thaht
format.

"""

import re
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


def _cha_cleanup(s):
    """Replacements to clean up punctuation, etc.

    Usually ok regardless of the corpus. We keep the timestamp in this
    version of the script.

    """
    if not re.search('[0-9]+_[0-9]+', s):
        return ''
    if re.match('\[- spa\]', s):
        return ''

    # remove undesired tags
    s = re.sub('@Media.*', '', s)
    s = re.sub('@Date.*', '', s)
    s = re.sub('@PID.*', '', s)
    s = re.sub('^....:.', '', s)
    s = re.sub('&[^ ]*', '', s)
    s = re.sub('[^ ]*@sspa', '', s)
    s = re.sub('\[[^[]*\]', '', s)
    s = re.sub('\(.+\)', '', s)
    s = re.sub('^[ ]*', '', s)

    # delete chars
    for c in (u'/".?!;<>,:\\”“'):
        s = s.replace(c, '')

    # replace by space
    for c in ('+', "' ", '  '):
        s = s.replace(c, ' ')

    # delete some tags
    for c in ('xxx', 'www', 'XXX', 'yyy', '@o', '@f', '@q', '@u', '@c'):
        s = s.replace(c, '')

    # TODO This should be outside the cha module and goes in the
    # preparator code directly...  NOTE check that the next set of
    # replacements for unusual spellings is adapted to your purposes
    for p in (
            ('allgone', 'all gone'),
            ('whaddaya', 'what do you'),
            ('whadda', 'what do'),
            ('haveto', 'have to'),
            ('hasto', 'has to'),
            ('outof', 'out of'),
            ('lotsof', 'lots of'),
            ('lotta', 'lots of'),
            ('alotof', 'a lot of'),
            ("wha\'s", "what's"),
            ("this\'s", 'this is'),
            ('chya', ' you'),
            ('tcha', 't you'),
            ('dya ', 'd you '),
            ('chyou', ' you'),
            ("dont you", "don\'t you"),
            ('wanta', 'wanna'),
            ("whats ", " what\'s "),
            ("'re", " are"),
            ("klenex", "kleenex"),
            ('yogourt', 'yogurt'),
            ('weee*', 'wee'),
            ('oooo*', 'oh'),
            (' oo ', ' oh '),
            ('ohh', 'oh'),
            (' im ', " I\'m ")):
        s = s.replace(p[0], p[1])

    return s.strip()


def clean(lines):
    """Return a list of cleaned utterances from a set of raw cha lines

    This function is a wrapper on the _cha_cleanup function

    """
    return (_cha_cleanup(l) for l in lines)
