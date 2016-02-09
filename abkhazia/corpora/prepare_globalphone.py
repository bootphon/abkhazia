#!/usr/bin/env python
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

"""Data preparation for the GlobalPhone multilingual corpus

For now only Mandarin and Vietnamese are supported. The wav
extraction step requires 'shorten' and 'sox' on the path.

"""

from abkhazia.corpora.utils import default_argument_parser
from abkhazia.corpora.globalphone import (
    MandarinPreparator,
    VietnamesePreparator)

# a custom main function to deals with the different languages
def main():
    """The command line entry for the GlobalPhone corpus preparation"""
    try:
        # all the supported languages mapped to their preparators
        preparators = {
            'Mandarin': MandarinPreparator,
            'Vietnamese': VietnamesePreparator
        }

        # add a language selection option to the arguments parser
        parser = default_argument_parser('GlobalPhone', __doc__)
        parser.add_argument(
            '-l', '--language', nargs='+', metavar='LANGUAGE',
            default=preparators.keys(), choices=preparators.keys(),
            help='specify the languages to prepare in {}, '
            'if this option is not specified prepare all the '
            'supported languages'.format(preparators.keys()))

        # prepare the corpus for the specified languages
        args = parser.parse_args()
        for language in args.language:
            corpus_prep = preparators[language](
                args.input_dir, args.output_dir, args.verbose)

            corpus_prep.prepare()
            if not args.no_validation:
                corpus_prep.validate()

    except Exception as err:
        print('fatal error: {}'.format(err))


if __name__ == '__main__':
    main()
