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
"""Implementation of the 'abkhazia align' command"""

import argparse
import sys

import abkhazia.kaldi.force_align as force_align

class AbkhaziaAlign(object):
    name = 'align'
    description = 'Compute forced-aligment'

    def __init__(self):
        # parse the arguments (ignore the first and second which are
        # 'abkahzia align')
        args = self.parser().parse_args(sys.argv[2:])

        # instanciate the kaldi recipe
        recipe = force_align.ForceAlign(
            args.input_dir, args.output_dir, args.verbose)

        # create and/or run the recipe
        if not args.only_run:
            recipe.create()
        if not args.no_run:
            recipe.run()

    @classmethod
    def parser(cls):
        """Return a parser for the align command"""
        parser = argparse.ArgumentParser(
            prog='abkhazia align',
            usage='%(prog)s <input-dir [--output-dir OUTPUT_DIR]\n'
            + ' '*23 + ('\n' + ' '*23).join([
                '[--help] [--verbose] [--no-run|--only-run]']),
            description=cls.description)

        group = parser.add_argument_group('directories')

        group.add_argument(
            'input_dir', metavar='input-dir',
            help='root directory of the abkhazia corpus to split')

        group.add_argument(
            '-o', '--output-dir', default=None,
            help='output directory of the splited corpus, '
            'if not specified use {}'.format(
                force_align.ForceAlign.default_output_dir()))

        parser.add_argument(
            '-v', '--verbose', action='store_true',
            help='display more messages to stdout')

        prop = group.add_mutually_exclusive_group()
        prop.add_argument(
            '--no-run', action='store_true',
            help='if specified create the recipe but dont run it')

        prop.add_argument(
            '--only-run', action='store_true',
            help='if specified, dont create the recipe but run it, '
            "'input_dir' must contain a top-level run.sh")

        return parser
