"""Provides some misc functions usefull in corpus preparation

@author: Mathieu Bernard

"""

import argparse
import os
import re


# TODO should be fixed during installation and not relative to __file__
ABKHAZIA_ROOT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..'))
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


def main(preparator):
    """A main function common to all the corpora preparators"""
    # print args
    # import sys

    # define an arguments parser
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir')
    parser.add_argument('output_dir')
    parser.add_argument('--no-validation', action='store_true')

    # parse the arguments string
    args = parser.parse_args()

    # instanciate the corpora
    p = preparator(args.input_dir, args.output_dir)

    # convert it to abkhazia format and validate it as needed
    p.prepare()
    if not args.no_validation:
        p.validate()
