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

import os
import shutil

from abkhazia.commands.abstract_command import AbstractCommand
import abkhazia.utils as utils
import abkhazia.kaldi.force_align as force_align


class AbkhaziaAlign(AbstractCommand):
    '''This class implements the 'abkahzia align' command'''
    name = 'align'
    description = 'compute forced-aligment'

    @classmethod
    def run(cls, args):
        # retrieve the corpus input directory
        if args.corpus.startswith(('/', './', '../', '~/')):
            corpus = args.corpus
        else:
            corpus = os.path.join(
                utils.config.get('abkhazia', 'data-directory'),
                args.corpus)

        # retrieve the output directory
        output_dir = corpus if args.output_dir is None else args.output_dir

        # if --force, remove any existing output_dir/force_align
        if args.force:
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
    def add_parser(cls, subparsers):
        """Return a parser for the align command"""
        # get basic parser init from AbstractCommand
        parser = super(AbkhaziaAlign, cls).add_parser(subparsers)

        parser.add_argument(
            '-v', '--verbose', action='store_true',
            help='display more messages to stdout')

        parser.add_argument(
            '-f', '--force', action='store_true',
            help='if specified, overwrite the result directory '
            '<output-dir>/force_align. If not specified but the '
            'directory exists, the program fails.')

        group = parser.add_argument_group('directories')

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
