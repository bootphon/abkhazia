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
import os
import shutil
import sys

import abkhazia.utils as utils
import abkhazia.kaldi.force_align as force_align


class AbkhaziaAlign(object):
    '''This class implemnts the 'abkahzia align' command

    Basically this class defines an argument parser, parses the
    arguments and instanciates a kaldi recipe. The recipe is run as
    needed.

    '''

    name = 'align'
    description = 'Compute forced-aligment'

    def __init__(self):
        # parse the arguments (ignore the first and second which are
        # 'abkahzia align')
        args = self.parser().parse_args(sys.argv[2:])

        # retrieve the corpus input directory
        if args.corpus.startswith(('/', './', '../')):
            corpus = args.corpus
        else:
            corpus = os.path.join(
                utils.config.get('abkhazia', 'data-directory'),
                args.corpus)

        # retrieve the output directory
        output_dir = corpus if args.output_dir is None else args.output_dir

        # if --force, remove any existing output_dir/split
        if args.force and not args.only_run:
            recipe_dir = os.path.join(output_dir, 'force_align')
            if os.path.exists(recipe_dir):
                print 'removing {}'.format(recipe_dir)
                shutil.rmtree(recipe_dir)

        # instanciate the kaldi recipe creator
        recipe = force_align.ForceAlign(corpus, output_dir, args.verbose)

        # finally create and/or run the recipe
        if not args.only_run:
            recipe.create()
        if not args.no_run:
            recipe.run()
            recipe.export()


    @staticmethod
    def long_description():
        """Return the docstring of the ForceAlign class"""
        return force_align.ForceAlign.__doc__.replace(' '*4, ' '*2).strip()


    @classmethod
    def parser(cls):
        """Return a parser for the align command"""
        prog = 'abkhazia align'
        spaces = ' '*(len(prog) + len(' <corpus>') + 8)

        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            prog=prog,
            # TODO add triphones params here
            usage='%(prog)s <corpus> [--output-dir <output-dir>]\n'
            + spaces + ('\n' + spaces).join([
                '[--help] [--verbose] [--force]',
                '[--no-optional-silence] [--no-pitch]',
                '[--no-run|--only-run']),
            description=cls.long_description())

        group = parser.add_argument_group('directories')

        parser.add_argument(
            '-v', '--verbose', action='store_true',
            help='display more messages to stdout')

        parser.add_argument(
            '-f', '--force', action='store_true',
            help='if specified, overwrite the result directory '
            '<output-dir>/force_align. If not specified but the '
            'directory exists, the program fails.')

        group.add_argument(
            'corpus', metavar='<corpus>',
            help="""
            the input abkhazia corpus to split. Must be a directory
            either relative to the abkhazia data directory ({0}) or
            relative/absolute on the filesystem. The following rule
            applies: if <corpus> starts with './', '../' or '/', path is
            guessed directly, else <corpus> is guessed as a subdir in
            {0}""".format(utils.config.get('abkhazia', 'data-directory')))

        group.add_argument(
            '-o', '--output-dir', default=None, metavar='<output-dir>',
            help='output directory, the forced alignment recipe is '
            'created in <output-dir>/force_align/s5. '
            'If not specified use <output-dir> = <corpus>.')


        prop = group.add_mutually_exclusive_group()
        prop.add_argument(
            '--no-run', action='store_true',
            help='if specified create the recipe but dont run it')

        prop.add_argument(
            '--only-run', action='store_true',
            help='if specified, dont create the recipe but run it')

        return parser
