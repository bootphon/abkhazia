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
"""Provides the Meta class for attaching metadata to abkhazia models"""

import datetime
import getpass
import socket


class Meta(object):
    """Store meta information about an object

    Attach and manage metadata to an abkhazia object, such as creation
    date, source and user.

    Attached data is dumped to a meta.txt file, must be a oneline str.

    """
    date_format = '%b %d %Y %H:%M:%S.%f'  # May 20 2016 12:42:39.705852

    def __init__(self, name='', source='', comment=''):
        self.date = datetime.datetime.now()
        self.user = getpass.getuser()
        self.host = socket.gethostname()
        self.name = str(name).replace('\n', '. ')
        self.source = str(source).replace('\n', '. ')
        self.comment = str(comment).replace('\n', '. ')

    @staticmethod
    def _load_token(token, lines):
        try:
            line = [l for l in lines if token in l][0]
            return ':'.join(line.split(':')[1:]).strip()
        except IndexError:
            return ''

    @classmethod
    def load(cls, meta):
        # read the meta file (removing commented lines)
        lines = [l.split('#')[0].strip() for l in open(meta, 'r').readlines()]

        _self = cls()
        _self.user = cls._load_token('user', lines)
        _self.host = cls._load_token('host', lines)
        _self.name = cls._load_token('name', lines)
        _self.source = cls._load_token('source', lines)
        _self.comment = cls._load_token('comment', lines)

        # parsing date string to datetime object can fail (because of
        # internationalization ?)
        try:
            _self.date = datetime.datetime.strptime(
                cls._load_token('date', lines), cls.date_format)
        except ValueError:
            _self.date = cls._load_token('date', lines)

        return _self

    def save(self, meta):
        with open(meta, 'w') as meta_file:
            for line in (
                    'date: {}'.format(self.date.strftime(self.date_format)),
                    'user: {}'.format(self.user),
                    'host: {}'.format(self.host),
                    'name: {}'.format(self.name),
                    'source: {}'.format(self.source),
                    'comment: {}'.format(self.comment)):
                meta_file.write(line + '\n')
