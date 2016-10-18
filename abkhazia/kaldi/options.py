# Copyright 2016 Thomas Schatz, Mathieu Bernard, Roland Thiolliere
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
"""Wrapper for getting/setting Kaldi optional parameters"""

import re
import shlex
import subprocess

from abkhazia.utils import bool2str
from abkhazia.kaldi.path import kaldi_path


class OptionEntry(object):
    """Entry read from / send to a Kaldi executable"""
    def __init__(self, help='', type=None, default=None, value=None):
        self.help = help
        self.type = type
        self.default = default
        self.value = value if value else default

    def __str__(self):
        """Return the value of an option as a string

        The returned value is converted to string according to its
        type.

        * For bool: True -> 'true'.
        * For list: [1, 2, 3] -> '"1 2 3"' (note the double quotes).
        * Else defailt str() cast

        """
        if self.type is bool:
            return bool2str(self.value)
        elif self.type is list:
            return '"' + ' '.join(str(i) for i in self.value) + '"'
        return str(self.value)


def make_option(name, help='', type=None, default=None, value=None):
    """Return a tuple (name, OptionEntry)"""
    return (name, OptionEntry(help, type, default, value))


def _get_default(name, entry, overload):
    """Default value of the option `name`, optionally overloaded

    Return overload[name] if existing, else entry.default

    """
    try:
        return overload[name]
    except KeyError:
        return entry.default


def _str2type(t):
    if not isinstance(t, str):
        return t
    # raise on unknown type
    return {'bool': bool,
            'int': int,
            'float': float,
            'string': str,
            'list': list}[t]


def _type2str(t):
    if isinstance(t, str):
        return t
    # raise on unknown type
    return {bool: 'bool',
            int: 'int',
            float: 'float',
            str: 'string',
            list: 'list'}[t]


def get_options(executable):
    """Return the options taken by `executable` as a dictionary of entries

    This function execute `executable --help` and parse the help
    message to build and return a dictionary of options[name] -> OptionEntry

    """
    try:
        # help message displayed on stderr with --help argument
        helpmsg = subprocess.Popen(
            shlex.split(executable + ' --help'),
            stderr=subprocess.PIPE,
            env=kaldi_path()).communicate()[1]
    except OSError:
        raise RuntimeError('No such executable "{}"'.format(executable))

    # parse the help to extract only the options paragraph (i.e. all
    # within the lines 'Options:' and 'Standard options:')
    lbegin = 0
    lend = 0
    for n, line in enumerate(helpmsg.split('\n')):
        if lbegin == 0 and line.startswith('Options:'):
            lbegin = n+1
        if lbegin != 0 and line.startswith('Standard options:'):
            lend = n-1
            break
    raw_options = (o.strip() for o in helpmsg.split('\n')[lbegin:lend])

    # parse each option line as an OptionEntry instance in a list
    options = {}
    for opt in raw_options:
        matched = re.match(
            '^--([a-zA-Z-0-9\-]+)\s+: (.*)\((.*), default = (.*)\)$', opt)
        options[matched.group(1)] = OptionEntry(
            help=matched.group(2).strip(),
            type=matched.group(3),
            default=matched.group(4),
            value=None)
    return options


def add_options(parser, options,
                action=lambda n: 'store', ignore=[], overload={}):
    """Add the arguments from `options` to the given `parser`

    This method calls the add_argument method of the parser for each
    optional argument read from a dictionary of (name, OptionEntry).

    Parameters:
    -----------

    parser: any object with a add_argument method (typically from the
        argparse module)

    options (dict): the options as (name, OptionEntry) in a dictionary

    action: a function(name) wich result is forwarded as the 'action'
        argument of the argparse add_argument function, optional

    ignore: list of option names to ignore in the executable options

    overload: dict of (option_name, default_value) to overload the
        default values from the executable    """

    def _format_help(entry, default):
        if isinstance(default, bool):
            default = bool2str(default)
        elif isinstance(default, list):
            default = '"' + ' '.join(str(i) for i in default) + '"'
        default = 'default is {}'.format(default)

        try:
            helpmsg = (entry.help[:-1] if entry.help[-1] == '.'
                       else entry.help) + ', '
        except IndexError:
            # entry.help is empty
            helpmsg = ''

        return ''.join((helpmsg, default))

    opt_iter = ((name, entry) for name, entry in sorted(options.iteritems())
                if name not in ignore)
    for name, entry in opt_iter:
        _type = _str2type(entry.type)
        _default = _get_default(name, entry, overload)
        if _type == bool:
            parser.add_argument(
                '--{}'.format(name),
                metavar='<true|false>',
                choices=['true', 'false'],
                default=_default,
                help=_format_help(entry, _default),
                action=action(name))
        elif _type == list:
            parser.add_argument(
                '--{}'.format(name),
                metavar='<int>',
                type=str, nargs='+', default=_default,
                help=_format_help(entry, _default),
                action=action(name))
        else:
            parser.add_argument(
                '--{}'.format(name),
                metavar='<{}>'.format(_type2str(entry.type)),
                type=_type, default=_default,
                help=_format_help(entry, _default),
                action=action(name))


def add_options_executable(
        parser, executable, action=lambda n: 'store', ignore=[], overload={}):
    """Add the arguments from `executable` to the given `parser`

    This method calls the add_argument method of the parser for each
    optional argument read from the executable optional arguments.

    Parameters:
    -----------

    parser: any object with a add_argument method (typically from the
        argparse module)

    executable: any Kaldi executable (not scripts from egs)

    action: a function(name) wich result is forwarded as the 'action'
        argument of the argparse add_argument function, optional

    ignore: list of option names to ignore in the executable options

    overload: dict of (option_name, default_value) to overload the
        default values from the executable

    """
    # iterate on the executable options while ignoring those who have to
    options = get_options(executable)
    add_options(parser, options,
                action=action, ignore=ignore, overload=overload)
