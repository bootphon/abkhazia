#!/usr/bin/env python
"""Command-line tool for preparing corpora to the abkhazia format

Use 'data_prep.py --help' to get info on command-line options

@author: Mathieu Bernard

"""

import argparse

from abkhazia.corpora.preparator import buckeye, xitsonga
from abkhazia.corpora.utils import DEFAULT_OUTPUT_DIR


CORPORA = [buckeye.BuckeyePreparator,
           xitsonga.XitsongaPreparator]
"""The list of corpora preparators"""


CORPORA_LIST = sorted([c.name for c in CORPORA])
"""The list of corpora names"""


def retrieve_preparator(name):
    """Return a preparator given its name, raise if not found"""
    for corpus in CORPORA:
        if corpus.name == name:
            return corpus
    raise IOError('{} is not a valid corpus name.\nChoose in {}'
                  .format(name, ', '.join(CORPORA_LIST)))


def parse_args():
    """Defines command-line arguments and parse them"""
    parser = argparse.ArgumentParser(
        description="""Prepare one of the supported corpora
                       to be used with abkhazia. Actually the supported
                       corpora are {}.""".format(
                           ', '.join(CORPORA_LIST)))

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='display the log messages on stdout')

    parser.add_argument('--no-validation', action='store_true',
                        help='disable the corpus validation.')

    parser.add_argument('corpus', choices=CORPORA_LIST,
                        help='name of the corpus to prepare, '
                        'must be in the names listed by the --list option')

    parser.add_argument('corpus_dir',
                        help='root directory of the raw corpus distribution')

    parser.add_argument('output_dir', nargs='?', default=None,
                        help='root directory of the prepared corpus')

    return parser.parse_args()


def main():
    """A main function common to all the corpora preparators

    This function basically does these successive steps:
    - parse the command line arguments
    - initialize the preparator of the specified corpus
    - prepare the corpus (convert it to the abkhazia format)
    - validate the prepared corpus if asked

    """
    # parse command line arguments
    args = parse_args()

    # retrieve the corpus preparator
    preparator = retrieve_preparator(args.corpus)

    # prepare the corpus
    corpus_prep = preparator(args.corpus_dir, args.output_dir, args.verbose)
    corpus_prep.prepare()
    if not args.no_validation:
        corpus_prep.validate()


if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print('Fatal error: {}'.format(err))
