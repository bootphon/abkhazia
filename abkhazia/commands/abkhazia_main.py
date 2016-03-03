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

import sys
import textwrap
import pkg_resources
import argcomplete, argparse

import abkhazia.utils as utils

from abkhazia.commands import (
    AbkhaziaPrepare,
    AbkhaziaSplit,
    AbkhaziaLanguage,
    AbkhaziaTrain,
    AbkhaziaDecode,
    AbkhaziaAlign)

__version__ = '0.2'


class Abkhazia(object):
    """Parse the input arguments and call the requested subcommand"""
    # the possible subcommand classes
    _command_classes = [
        AbkhaziaPrepare,
        AbkhaziaSplit,
        AbkhaziaLanguage,
        AbkhaziaTrain,
        AbkhaziaDecode,
        AbkhaziaAlign
    ]

    # a string describing abkhazia and its subcommands
    description = (
        'ABX and kaldi experiments on speech corpora made easy,\n'
        "type 'abkhazia <command> --help' for help on a specific command")

    def load_config(self):
        """Load the config file optionally given by --config argument

        Return the splited argument strins taken from sys.argv, with
        '--config <config-file>' removed

        """
        parser = argparse.ArgumentParser(add_help=False)

        class _ConfigAction(argparse.Action):
            def __call__(self, parser, namespace, values, option_string=None):
                # TODO list config files later (log it in command __init__)
                print 'loading configuration from {}'.format(values)
                utils.config.read(values)

        # add a configuration argument
        parser.add_argument(
            '-c', '--config', metavar='<config-file>', action=_ConfigAction)

        return parser.parse_known_args()[1]

    def init_parser(self):
        """Return an argument parser initialized form abkhazia subcommands"""
        # create the top-level parser
        parser = argparse.ArgumentParser(
            prog='abkhazia',
            formatter_class=argparse.RawTextHelpFormatter,
            description=textwrap.dedent(self.description))

        # add a version description argument
        parser.add_argument(
            '--version', action='version', version='%(prog)s-' + __version__)

        # this is a fake argument, as --config has been parsed in
        # self.load_config(). But we need it to have the option
        # documented on 'abkhazia --help'
        parser.add_argument(
            '-c', '--config', metavar='<config-file>', default=None,
            help='overload default abkhazia configuration with parameters\n'
            'defined in <config-file>, default configuration is read from\n{}'
            .format(utils.AbkhaziaConfig.default_config_file()))

        # register the subcommands parsers, and list their name and
        # descripion on --help
        subparsers = parser.add_subparsers(
            metavar='<command>',
            help='possible commands are:\n' +
            '\n'.join((' {} - {}'
                       .format(c.name + ' '*(8-len(c.name)), c.description)
                       for c in self._command_classes)))

        for command in self._command_classes:
            command.add_parser(subparsers)

        return parser

    def __init__(self):
        # at first, we load optional config file (--config
        # option). Values read from configuration can now be displayed
        # as default values in --help messages
        argv = self.load_config()

        # init the parser and subparsers for abkhazia
        parser = self.init_parser()

        # enable autocompletion and parse arguments
        argcomplete.autocomplete(parser)
        args = parser.parse_args(argv)

        # call the run() method of the parsed subcommand
        args.command(args)


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
