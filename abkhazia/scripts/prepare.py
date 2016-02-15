# coding: utf-8

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
"""'abkhazia prepare' command"""

import argparse
import sys
import textwrap

# TODO don't import all the preps here !! Do something with filenames
# introspection instead
from abkhazia.prepare.prepare_aic import AICPreparator
from abkhazia.prepare.prepare_buckeye import BuckeyePreparator
from abkhazia.prepare.prepare_csj import CSJPreparator
from abkhazia.prepare.prepare_librispeech import LibriSpeechPreparator
from abkhazia.prepare.prepare_wsj import WallStreetJournalPreparator
from abkhazia.prepare.prepare_xitsonga import XitsongaPreparator

# TODO fix globalphone main to class


def format_key(key):
    # desired length is len('librispeech ')
    return key + ' '*(12 - len(key))

def format_url(item, sep='\n'):
    if isinstance(item, str):
        return sep + item
    else:
        return sep + sep.join(item)

class AbkhaziaPrepare(object):
    name = 'prepare'
    description = 'Prepare a corpus for use with abkhazia'

    supported_corpora = dict((n, c) for n, c in (
        ('aic', AICPreparator),
        ('buckeye', BuckeyePreparator),
        ('csj', CSJPreparator),
        ('librispeech', LibriSpeechPreparator),
        ('wsj', WallStreetJournalPreparator),
        ('xitsonga', XitsongaPreparator)))

    def __init__(self):
        long_description = (
            self.description + '\n'
            + "type 'abkhazia prepare <corpus> --help' for help "
            + "on a specific corpus\n\n"
            + 'supported corpora are:\n    '
            + '\n    '.join(
                ('{} - {}{}'.format(
                    format_key(key),
                    self.supported_corpora[key].description,
                    format_url(self.supported_corpora[key].url, '\n\t\t   ')))
                for key in sorted(self.supported_corpora.iterkeys())))

        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            usage='abkhazia prepare <corpus> [--help] [<args>]',
            description=textwrap.dedent(long_description))

        parser.add_argument(
            'corpus',
            metavar='corpus',
            choices=sorted(
                (c.strip().lower() for c in self.supported_corpora.keys())),
            help='the speech corpus to prepare')

        corpus = parser.parse_args([sys.argv[2]]).corpus
        preparator = self.supported_corpora[corpus]
        preparator.main(sys.argv[3:])
