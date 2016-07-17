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
"""Wrapper for getting/setting optional parameters of a Kaldi executable"""

import re
import shlex
import subprocess

from abkhazia.kaldi.path import kaldi_path


class OptionEntry(object):
    """Entry read from / send to a Kaldi executable"""
    def __init__(self, help='', type=None, default=None, value=None):
        self.help = help
        self.type = type
        self.default = default
        self.value = value


def _get_default(name, entry, overload):
    """Default value of the option `name`, optionally overloaded

    Return overload[name] if existing, else entry.default

    """
    try:
        return overload[name]
    except KeyError:
        return entry.default


_type_dict = {
    'bool': bool,
    'int': int,
    'float': float,
    'string': str}


def get_options(executable):
    """Return the options taken by `executable` as a dictionary of entries"""
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


def add_options_arguments(
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
    opt_iter = ((name, entry) for name, entry in sorted(options.iteritems())
                if name not in ignore)

    for name, entry in opt_iter:
        if entry.type == 'bool':
            parser.add_argument(
                '--{}'.format(name),
                metavar='<true|false>',
                choices=['true', 'false'],
                default=_get_default(name, entry, overload),
                help=(entry.help[:-1] if entry.help[-1] == '.'
                      else entry.help) + ', default is %(default)s',
                action=action(name))
        else:
            parser.add_argument(
                '--{}'.format(name),
                metavar='<{}>'.format(entry.type),
                type=_type_dict[entry.type],
                default=_get_default(name, entry, overload),
                help=(entry.help[:-1] if entry.help[-1] == '.'
                      else entry.help) + ', default is %(default)s',
                action=action(name))
