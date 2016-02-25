#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
#
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
"""The abkhazia entry point from command line"""

import argcomplete, argparse
import pkg_resources
import sys
import textwrap

from abkhazia.commands import (
    AbkhaziaPrepare,
    AbkhaziaSplit,
    AbkhaziaTrain,
    AbkhaziaDecode,
    AbkhaziaAlign)


class Abkhazia(object):
    """Parse the first input argument and call the requested subcommand"""
    # the possible subcommand classes
    _command_classes = [
        AbkhaziaPrepare,
        AbkhaziaSplit,
        AbkhaziaTrain,
        AbkhaziaDecode,
        AbkhaziaAlign
    ]

    # a dict mapping each command name to class
    commands = [(c.name, c) for c in _command_classes]

    # a string describing abkhazia and its subcommands
    description = (
        'ABX and kaldi experiments on speech corpora made easy,\n'
        "type 'abkahzia <command> --help' for help on a specific command"
        + '\n\n'
        + 'possible commands are:\n    '
        + '\n    '.join(('{}\t{}'.format(n, c.description)
                         for n, c in commands)))

    def __init__(self):
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=textwrap.dedent(self.description),
            usage='abkhazia <command> [--help] [<args>]')

        parser.add_argument('command', help='Subcommand to run',
                            metavar='command',
                            choices=[n for n, _ in self.commands])

        argcomplete.autocomplete(parser)
        try:
            # parse only the first argument, must be a valid command
            command_name = parser.parse_args([sys.argv[1]]).command
        except IndexError:
            print 'You must provide a subcommand'
            parser.print_help()
            sys.exit(1)

        try:
            # get the command class from its name
            command = dict(self.commands)[command_name]
        except KeyError:
            print 'Unrecognized command: {}'.format(command_name)
            parser.print_help()
            sys.exit(1)

        # execute the command (ie. instanciates the command class)
        command()


class CatchExceptions(object):
    """A decorator wrapping 'function' in a try/except block

    When an exception occurs, display a user friendly message before
    exiting.

    """
    def __init__(self, function):
        self.function = function

    def __call__(self):
        try:
            self.function()

        except (IOError, OSError, RuntimeError) as err:
            print 'fatal error: {}'.format(err)
            sys.exit(1)

        except pkg_resources.DistributionNotFound:
            print ('fatal error: abkhazia package not found\n'
                   'please install abkhazia on your platform')
            sys.exit(1)

        except KeyboardInterrupt:
            print 'keyboard interruption, exiting'
            sys.exit(1)


# when debugging the abkhazia command-line tools from a terminal, it
# can be usefull to don't catch any exception, so the full error
# traceback error is printed. To do so, just comment the following
# line
@CatchExceptions
def main():
    """abkhazia main entry point in command line"""
    Abkhazia()

if __name__ == '__main__':
    main()
