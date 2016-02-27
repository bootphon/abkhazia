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
