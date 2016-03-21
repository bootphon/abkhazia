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
# along with abkhazia. If not, see <http://www.gnu.org/licenses/>.
"""Provides the AbstractCommand class"""


import argparse
import os
import shutil
import textwrap

import abkhazia.utils as utils


class AbstractCommand(object):
    """The base class of all abkhazia commands

    All the abkhazia commands must implement this interface.

    Basically this class defines the methods add_parser() and run(),
    respectively defining the command parser and how to run it from
    the parsed arguments.

    """
    name = NotImplemented
    """The command name, as called from command-line"""

    description = NotImplemented
    """A command description"""

    @classmethod
    def add_parser(cls, subparsers):
        """Add the command's parser to the `subparsers`

        This method implements only minimal parsing and should be
        overloaded in child classes. Basically you may want to add
        some arguments to parse...

        """
        # add a new subparser for the command
        parser = subparsers.add_parser(cls.name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter

        # link args.command to the run() method
        parser.set_defaults(command=cls.run)

        # add a brief description of the command
        parser.description = textwrap.dedent(cls.description)

        # add a --verbose option to all commands
        parser.add_argument(
            '-v', '--verbose', action='store_true',
            help='display more messages to stdout')

        return parser

    @classmethod
    def run(cls, args):
        """Run the command according to the parsed argumetns in `args`"""
        raise NotImplementedError


class AbstractPreparedCommand(AbstractCommand):
    """Base class for abkhazia commands other than 'prepare'

    Overloads the add_parser() method with a --force option, as well
    as input and output directories arguments. This class also define
    a prepare_for_run() method which implement the behavior of these
    parameters.

    """
    @classmethod
    def add_parser(cls, subparsers):
        # get basic parser init from AbstractCommand
        parser = super(AbstractPreparedCommand, cls).add_parser(subparsers)

        # add a --force option to all commands
        parser.add_argument(
            '-f', '--force', action='store_true',
            help='if specified, overwrite the output directory. '
            'If not specified but the directory exists, the program fails.')

        dir_group = parser.add_argument_group('directories')

        dir_group.add_argument(
            'corpus', metavar='<corpus>',
            help="""the abkhazia corpus to process. Must be a directory either
            relative to the abkhazia data directory ({0}) or
            relative/absolute on the filesystem. The following rule
            applies: if <corpus> starts with './' , '../', '~/' or
            '/', path is guessed directly, else <corpus> is guessed as
            a subdirectory of {0}""".format(
                utils.config.get('abkhazia', 'data-directory')))

        dir_group.add_argument(
            '-o', '--output-dir', default=None, metavar='<output-dir>',
            help='output directory, the output data is wrote to '
            '<output-dir>/{}. If not specified use <output-dir>=<corpus>.'
            .format(cls.name))

        return parser, dir_group

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

        return os.path.abspath(corpus), os.path.abspath(output_dir)


class AbstractRecipeCommand(AbstractPreparedCommand):
    """Base class for all commands relying on kaldi"""
    @classmethod
    def add_parser(cls, subparsers):
        # get basic parser init from AbstractCommand
        parser, dir_group = super(AbstractRecipeCommand, cls).add_parser(subparsers)

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

        return parser, dir_group
