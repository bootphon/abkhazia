#!/usr/bin/env python
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

import argparse
import sys
import textwrap

from abkhazia.commands.abkhazia_prepare import AbkhaziaPrepare
from abkhazia.commands.abkhazia_split import AbkhaziaSplit
from abkhazia.commands.abkhazia_train import AbkhaziaTrain
from abkhazia.commands.abkhazia_decode import AbkhaziaDecode
from abkhazia.commands.abkhazia_align import AbkhaziaAlign


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
    _commands = [(c.name, c) for c in _command_classes]

    # a string describing abkhazia and its subcommands
    description = (
        'ABX and kaldi experiments on speech corpora made easy,\n'
        "type 'abkahzia <command> --help' for help on a specific command"
        + '\n\n'
        + 'possible commands are:\n    '
        + '\n    '.join(('{}\t{}'.format(n, c.description)
                         for n, c in _commands)))

    def __init__(self):
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=textwrap.dedent(self.description),
            usage='abkhazia <command> [--help] [<args>]')

        parser.add_argument('command', help='Subcommand to run')

        try:
            # parse only the first argument, must be a valid command
            command_name = parser.parse_args([sys.argv[1]]).command
        except IndexError:
            print 'You must provide a subcommand'
            parser.print_help()
            exit(1)

        try:
            command = dict(self._commands)[command_name]
        except KeyError:
            print 'Unrecognized command: {}'.format(command_name)
            parser.print_help()
            exit(1)

        # execute the command (ie. instanciates the command class)
        command()

def main():
    """call Abkhazia()"""
    # Abkhazia(); sys.exit(0)
    try:
        Abkhazia()
    except (IOError, OSError, RuntimeError) as err:
        print 'fatal error: {}'.format(err)
    except KeyboardInterrupt:
        print 'keyboard interruption, exiting'

if __name__ == '__main__':
    main()
