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
"""Provides the AbstractCommand class"""

import os
import shutil

import abkhazia.utils as utils


class AbstractCommand(object):
    """The base class of all abkhazia commands

    All the abkhazia commands must implement this interface.

    Basically this class defines an argument parser, parses the
    arguments and split a corpus in train and test subsets. The
    spliting operation is delegated to the split.SplitCorpus class.

    """
    name = NotImplemented
    """The command name, as called from command-line"""

    description = NotImplemented
    """A one-line command description"""

    @classmethod
    def add_parser(cls, subparsers):
        """Add the command's parser to the `subparsers`

        This method implements only minimal parsing and should be
        overloaded in child classes. Basically you may want to add
        some arguments to parse...

        """
        # add a new subparser for the command
        parser = subparsers.add_parser(cls.name)

        # link args.command to the run() method
        parser.set_defaults(command=cls.run)

        # add a brief description of the command
        parser.description = cls.description

        return parser

    @classmethod
    def run(cls, args):
        """Run the command according to the parsed argumetns in `args`"""
        raise NotImplementedError


class AbstractPreparedCommand(AbstractCommand):
    """Base class for abkhazia commands other than 'prepare'"""
    @classmethod
    def add_parser(cls, subparsers):
        # get basic parser init from AbstractCommand
        parser = super(AbstractPreparedCommand, cls).add_parser(subparsers)

        parser.add_argument(
            '-v', '--verbose', action='store_true',
            help='display more messages to stdout')

        parser.add_argument(
            '-f', '--force', action='store_true',
            help='if specified, overwrite the result directory '
            '<output-dir>/split. If not specified but the directory exists, '
            'the program fails.')

        group = parser.add_argument_group('directories')

        group.add_argument(
            'corpus', metavar='<corpus>',
            help="""
            the input abkhazia corpus to split. Must be a directory
            either relative to the abkhazia data directory ({0}) or
            relative/absolute on the filesystem. The following rule
            applies: if <corpus> starts with './' , '../' or '/', path is
            guessed directly, else <corpus> is guessed as a subdir in
            {0}""".format(utils.config.get('abkhazia', 'data-directory')))

        group.add_argument(
            '-o', '--output-dir', default=None, metavar='<output-dir>',
            help='output directory, the splited corpus is created in '
            '<output-dir>/split. '
            'If not specified use <output-dir> = <corpus>.')

        return parser

    @classmethod
    def prepare_for_run(cls, args):
        # retrieve the corpus input directory
        if args.corpus.startswith(('/', './', '../', '~/')):
            corpus = args.corpus
        else:
            corpus = os.path.join(
                utils.config.get('abkhazia', 'data-directory'),
                args.corpus)

        # retrieve the output directory
        output_dir = corpus if args.output_dir is None else args.output_dir

        # if --force, remove any existing output_dir/cls.name
        if args.force:
            _dir = os.path.join(output_dir, cls.name)
            if os.path.exists(_dir):
                print 'removing {}'.format(_dir)
                shutil.rmtree(_dir)

        return corpus, output_dir


class AbstractRecipeCommand(AbstractPreparedCommand):
    """Base class for all commands relying on kaldi"""
    @classmethod
    def add_parser(cls, subparsers):
        # get basic parser init from AbstractCommand
        parser = super(AbstractRecipeCommand, cls).add_parser(subparsers)

        parser.add_argument(
            '-j', '--njobs', type=int, default=4, metavar='<njobs>',
            help='number of jobs to launch when doing no-clustered '
            'parallel computations (mainly for wav analysis). '
            'Default is to launch %(default)s jobs.')

        group = parser.add_argument_group('command options')

        prop = group.add_mutually_exclusive_group()
        prop.add_argument(
            '--no-run', action='store_true',
            help='if specified create the recipe but dont run it')

        prop.add_argument(
            '--only-run', action='store_true',
            help='if specified, dont create the recipe but run it')

        return parser
