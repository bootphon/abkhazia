# Copyright 2016 Thomas Schatz, Xuan-Nga Cao, Mathieu Bernard
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
"""Provides base classes for abkhazia commands

This module defines a hierarchy of 3 classes, each of the command-line
tools (aka abkhazia commands) must inherit from one of these classes.

AbstractCommand -> prepare
AbstractCoreCommand -> split
AbstractKaldiCommand -> language, acoustic, align, decode

Basically this classes defines the methods add_parser() and run(),
respectively defining the command parser and how to run it from the
parsed arguments.

"""

import argparse
import os
import shutil
import textwrap

import abkhazia.utils as utils


class AbstractCommand(object):
    """The base class of all abkhazia commands"""
    name = NotImplemented
    """The command name, as called from command-line"""

    description = NotImplemented
    """A command description"""

    @classmethod
    def add_parser(cls, subparsers, name=None):
        """Add the command's parser to the `subparsers`

        This method implements only minimal parsing and should be
        overloaded in child classes. Basically you may want to add
        some parameters and options to your command.

        If name is None, take cls.name

        """
        if name is None:
            name = cls.name

        # add a new subparser for the command
        parser = subparsers.add_parser(name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter

        # link args.command to the run() method
        parser.set_defaults(command=cls.run)

        # add a brief description of the command
        parser.description = textwrap.dedent(cls.description)

        # add a --verbose option to all commands
        parser.add_argument(
            '-v', '--verbose', action='store_true',
            help='display more messages to stdout')

        # add a --log option for non default log files
        parser.add_argument(
            '--log', default=None, metavar='<file>',
            help='file to write log messages, default is {} '
            'in the output directory'.format(name + '.log'))

        return parser

    @classmethod
    def run(cls, args):
        """Run the command according to the parsed arguments in `args`"""
        raise NotImplementedError


class AbstractCoreCommand(AbstractCommand):
    """Base class for abkhazia commands other than 'prepare'

    Overloads the add_parser() method with a --force option, as well
    as input and output directories arguments.

    This class also defines a parse_input_output() method which
    implement the behavior of these parameters as described in the
    add_parser() method.

    """
    @classmethod
    def add_parser(cls, subparsers, name=None):
        if name is None:
            name = cls.name

        # get basic parser init from AbstractCommand
        parser = super(AbstractCoreCommand, cls).add_parser(
            subparsers, name=name)

        # add a --force option to all commands
        parser.add_argument(
            '--force', action='store_true',
            help='if specified, overwrite the output directory. '
            'If not specified but the directory exists, exit with error')

        # add a --validate option
        parser.add_argument(
            '--validate', action='store_true',
            help=('''if specified, validate the corpus before any
            other processing, ensure corpus data are consistent'''))

        dir_group = parser.add_argument_group('directories')

        # add a <corpus> mandatory parameter
        dir_group.add_argument(
            'corpus', metavar='<corpus>', help="""
            abkhazia corpus is read from <corpus>/data. Must be an
            existing directory, can be relative to the abkhazia data
            directory ({0})"""
            .format(utils.config.get('abkhazia', 'data-directory')))

        # add a --output-dir option
        dir_group.add_argument(
            '-o', '--output-dir', default=None, metavar='<output-dir>',
            help='output directory, the output data is wrote to '
            '<output-dir>/{}, if not specified use <output-dir>=<corpus>.'
            .format(name))

        return parser, dir_group

    @staticmethod
    def _parse_corpus_dir(corpus):
        """Parse the corpus input directory as specified in help message

        If `corpus` doesn't start with './' , '../', '~/' or '/', the
        following rule applies: `corpus` is guessed as a subdirectory
        of 'abkhazia.data-directory' from config file and, if not
        found, as a subdirectory of the current working directory.

        """
        if not corpus.startswith(('/', '.', '../', '~/')):
            # try to find the corpus in abkhazia data directory
            _corpus = os.path.join(
                utils.config.get('abkhazia', 'data-directory'), corpus)
            if os.path.isdir(_corpus):
                corpus = _corpus
        return os.path.abspath(corpus)

    @classmethod
    def _parse_output_dir(cls, output, corpus, name=None, force=False):
        """Parse the output directory as specified in help message"""
        if name is None:
            name = cls.name

        # append the command name
        output = os.path.abspath(
            os.path.join(corpus, name) if output is None else output)

        # if --force, remove any existing output_dir
        if force and os.path.exists(output):
            print 'overwriting {}'.format(output)
            shutil.rmtree(output)

        return output

    @classmethod
    def _parse_io_dirs(cls, args, name=None):
        """Return (corpus_dir, output_dir) parsed form `args`"""
        if name is None:
            name = cls.name

        _input = cls._parse_corpus_dir(args.corpus)
        _output = cls._parse_output_dir(
            args.output_dir, _input, name, args.force)
        return os.path.join(_input, 'data'), _output

    @classmethod
    def _parse_aux_dir(cls, corpus_dir, arg, name=None):
        if name is None:
            name = cls.name

        return (os.path.join(os.path.dirname(corpus_dir), name)
                if arg is None else os.path.abspath(arg))


class AbstractKaldiCommand(AbstractCoreCommand):
    """Base class for commands relying on Kaldi recipes

    Adds a --recipe option that do not remove the Kaldi recipe
    directory and a --njobs option for parallel processing

    """
    @classmethod
    def add_parser(cls, subparsers, name=None):
        if name is None:
            name = cls.name

        # get basic parser init from AbstractCommand
        parser, dir_group = super(
            AbstractKaldiCommand, cls).add_parser(subparsers, name)

        # add a --recipe option
        parser.add_argument(
            '--recipe', action='store_true', help="""
            put the Kaldi recipe in <output_dir>/recipe, by default the recipe
            is deleted""")

        # add a --njobs option
        parser.add_argument(
            '-j', '--njobs', type=int, metavar='<njobs>',
            default=utils.default_njobs(),
            help="""number of jobs for parallel computation, default is
            to launch %(default)s jobs.""")

        return parser, dir_group
