"""Provides some misc functions usefull in corpus preparation"""

import os
import re

def list_files_with_extension(directory, extension):
    """Return the list of all files in the directory hierarchy with the given extension"""
    # the regular expression to match in filenames
    expr = '(.*)\.' + extension + '$'

    # build the list of matching files
    l = []
    for path, _, files in os.walk(directory):
        l += [os.path.join(path, f) for f in files if re.match(expr, f)]

    return l


def main(preparator, args):
    """A main function common to all the corpora preparators"""
    # define an arguments parser
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir')
    parser.add_argument('output_dir')
    parser.add_argument('--no-validation', action='store_true')

    # parse the arguments string
    args = parser.parse_args(args)

    # instanciate the corpora
    p = preparator(args.input_dir, args.output_dir)

    # convert it to abkhazia format and validate it as needed
    p.prepare()
    if not args.no_validation:
        p.validate()
