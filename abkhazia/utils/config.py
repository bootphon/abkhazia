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
"""Binding to the abkhazia configuration file"""

import ConfigParser
import os
import pkg_resources as pkg


def get_config(config_file=None):
    """Return a ConfigParser with the abkhazia configuration loaded

    The function raises OSError if the configuration is not found

    """
    # if file not specified, try to get the installed one
    if config_file is None:
        try:
            config_file = pkg.resource_filename(
                pkg.Requirement.parse('abkhazia'), 'share/abkhazia.cfg')
        except pkg.DistributionNotFound:
            pass

    # if not found, try to get it relatively to this file
    if config_file is None or not os.path.isfile(config_file):
        config_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', 'share/abkhazia.cfg')

    if config_file is None or not os.path.isfile(config_file):
        raise OSError('abkhazia configuration file not found {}'
                      .format(config_file))

    conf = ConfigParser.ConfigParser()
    conf.read(config_file)
    return conf
