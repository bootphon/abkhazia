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
import multiprocessing
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

        # TODO add a --log <file> option for non default log files
        return parser

    @classmethod
    def run(cls, args):
        """Run the command according to the parsed arguments in `args`"""
        raise NotImplementedError

    @classmethod
    def _default_njobs(cls, nj_queue=20):
        """Return `nj_queue` if running on a queue, ncores if running locally

        Default for `nj_queue` is 20, the standard number of jobs for
        features computation in the kaldi WSJ recipe.

        """
        cmd = utils.config.get('kaldi', 'train-cmd')
        return nj_queue if 'queue' in cmd else multiprocessing.cpu_count()


class AbstractRecipeCommand(AbstractCommand):
    """Base class for abkhazia commands other than 'prepare'

    Overloads the add_parser() method with a --force option, as well
    as input and output directories arguments. This class also defines
    a prepare_for_run() method which implement the behavior of these
    parameters.

    """
    @classmethod
    def add_parser(cls, subparsers):
        # get basic parser init from AbstractCommand
        parser = super(AbstractRecipeCommand, cls).add_parser(subparsers)

        # add a --force option to all commands
        parser.add_argument(
            '-f', '--force', action='store_true',
            help='if specified, overwrite the output directory. '
            'If not specified but the directory exists, the program fails.')

        dir_group = parser.add_argument_group('directories')

        # TODO simplify this! Implicit read in filesystem if failed in
        # abkhazia data directory
        dir_group.add_argument(
            'corpus', metavar='<corpus>',
            help="""the abkhazia corpus to process is read from <corpus>/data.
            Must be a directory either relative to the abkhazia data directory
            ({0}) or relative/absolute on the filesystem. The
            following rule applies: if <corpus> starts with './' ,
            '../', '~/' or '/', path is guessed directly, else
            <corpus> is guessed as a subdirectory of {0}""".format(
                utils.config.get('abkhazia', 'data-directory')))

        dir_group.add_argument(
            '-o', '--output-dir', default=None, metavar='<output-dir>',
            help='output directory, the output data is wrote to '
            '<output-dir>/{}, if not specified use <output-dir>=<corpus>.'
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
        corpus = os.path.abspath(corpus)

        # retrieve the output directory, append the command name as
        # specified in the parser help message
        output_dir = os.path.join(
            corpus if args.output_dir is None else args.output_dir,
            cls.name)
        output_dir = os.path.abspath(output_dir)

        # if --force, remove any existing output_dir
        if args.force:
            if os.path.exists(output_dir):
                print 'overwriting {}'.format(output_dir)
                shutil.rmtree(output_dir)

        return corpus, output_dir
