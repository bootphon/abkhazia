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
"""Binding to the abkhazia configuration file"""

import ConfigParser
import os
import pkg_resources as pkg


class AbkhaziaConfig(object):
    """Return a ConfigParser with the default abkhazia configuration

    The function raises OSError if the configuration is not found

    """
    @staticmethod
    def default_config_file():
        """Return the default abkhazia configuation file

        Look for 'share/abkhazia.cfg' from pkg_resources, if not
        found, look for __file__/../share/abkhazia.cfg, else raise
        OSError.

        """
        try:
            return pkg.resource_filename(
                pkg.Requirement.parse('abkhazia'),
                'abkhazia/share/abkhazia.cfg')
        except pkg.DistributionNotFound:
            config_file = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                '..', 'share/abkhazia.cfg')

            if not os.path.isfile(config_file):
                raise OSError('abkhazia configuration file not found {}'
                              .format(config_file))

            return config_file

    def __init__(self):
        self.conf = ConfigParser.ConfigParser()
        self.conf.readfp(open(self.default_config_file(), 'r'))

# by defining config at module level, we ensure the configuration file
# is load only once, the first this module is imported
config = AbkhaziaConfig().conf
