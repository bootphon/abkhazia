#!/usr/bin/env python
# coding: utf-8

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
