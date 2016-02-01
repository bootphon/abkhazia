"""Provides some misc functions usefull in corpus preparation

@author: Mathieu Bernard

"""

import argparse
import os
import re
import shlex
import shutil
import subprocess


# TODO should be fixed during installation and not relative to __file__
ABKHAZIA_ROOT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../..'))
"""The absolute to the Abkhazia installation directory"""


# TODO should go in a config file
DEFAULT_OUTPUT_DIR = os.path.join(ABKHAZIA_ROOT_DIR, 'corpora')
"""The default output directory for prepared corpora"""


def list_files_with_extension(directory, extension):
    """Return a list of all files of given extension in directory hierarchy"""
    # the regular expression to match in filenames
    expr = r'(.*)' + extension + '$'

    # build the list of matching files
    matched = []
    for path, _, files in os.walk(directory):
        matched += [os.path.join(path, f) for f in files if re.match(expr, f)]
    return matched


def flac2wav(flac, wav):
    """Convert a flac file to the wav format

    'flac' must be an existing flac file
    'wav' is the filename of the created file

    This method lies on the 'flac --decode' system command

    """
    command = 'flac --decode -f {} -o {}'.format(flac, wav)
    subprocess.call(shlex.split(command))


def default_argument_parser(name, description):
    """Return a default argument parser for corpus preparation"""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='display more messages to stdout '
                        '(this can be a lot)')

    parser.add_argument('--no-validation', action='store_true',
                        help='disable the corpus validation step')


    corpus = parser.add_argument_group('corpus preparation arguments')

    corpus.add_argument('-o', '--output-dir', default=None,
                        help='root directory of the prepared corpus, '
                        'if not specified use {}'
                        .format(os.path.join(DEFAULT_OUTPUT_DIR, name)))

    corpus.add_argument('input_dir',
                        help='root directory of the raw corpus distribution, '
                        'must be an existing directory on the filesystem')

    return parser


def main(preparator, description, argparser=default_argument_parser):
    """A main function common to all the corpora preparators

    This function basically does these successive steps:
    - parse the command line arguments
    - initialize the preparator of the specified corpus
    - prepare the corpus (convert it to the abkhazia format)
    - validate the prepared corpus if asked

    """
    try:
        # parse command line arguments
        args = argparser(preparator.name, description).parse_args()

        # prepare the corpus
        corpus_prep = preparator(args.input_dir, args.output_dir, args.verbose)
        corpus_prep.prepare()
        if not args.no_validation:
            corpus_prep.validate()
    except Exception as err:
        print('fatal error: {}'.format(err))
