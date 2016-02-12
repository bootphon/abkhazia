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
"""Provides some misc functions usefull in corpus preparation"""

import argparse
import os
import textwrap

from abkhazia.utils.config import get_config


DEFAULT_OUTPUT_DIR = os.path.join(
    get_config().get('abkhazia', 'data-directory'), 'corpora')
"""The default directory for prepared corpora is data-directory/corpora"""


def default_argument_parser(name, description):
    """Return a default argument parser for corpus preparation"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(description))

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='display more messages to stdout '
                        '(this can be a lot)')

    parser.add_argument('-j', '--njobs', type=int, default=4,
                        help='number of jobs to launch when doing parallel '
                        'computations (mainly for wav conversion). '
                        'Default is to launch 4 jobs.')

    parser.add_argument('-o', '--output-dir', default=None,
                        help='root directory of the prepared corpus, '
                        'if not specified use {}'
                        .format(os.path.join(DEFAULT_OUTPUT_DIR, name)))

    parser.add_argument('--no-validation', action='store_true',
                        help='disable the corpus validation step')

    parser.add_argument('input_dir',
                        help='root directory of the raw corpus distribution, '
                        'must be an existing directory on the filesystem')

    return parser


def default_main(preparator, description, argparser=default_argument_parser):
    """A default main function for corpora preparators

    This function basically does these successive steps:
    - parse the command line arguments
    - initialize the preparator of the specified corpus
    - prepare the corpus (convert it to the abkhazia format)
    - validate the prepared corpus if asked

    """
    try:
        args = argparser(preparator.name, description).parse_args()

        corpus_prep = preparator(
            args.input_dir, args.output_dir, args.verbose, args.njobs)

        corpus_prep.prepare()
        if not args.no_validation:
            corpus_prep.validate()

    except Exception as err:
        print('fatal error: {}'.format(err))
    except (KeyboardInterrupt, SystemExit):
        print('exiting')
