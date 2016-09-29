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
"""Provides the AbkhaziaConfig class and the config global variable

The `config` variable store the default abkhazia configuration and is
accessible from anywhere in the abkhazia package. It is designed to be
instanciated once and only once, the first time this module is
imported.

Exemple:
--------

* To use the default config file:
..

  from abkhazia.utils import config

  data_directory = config.get('abkhazia', 'data-directory')
  prune_lexicon = config.get('split', 'prune-lexicon')
  lm_order = config.getint('language', 'model-order')

* To load a custom config file:
..
  custom_config = config.AbkhaziaConfig('/path/to/my-custom-config.cfg')
  custom_config.get(...)

"""

import ConfigParser
import os
import pkg_resources as pkg


class AbkhaziaConfig(object):
    """Hold the abkhazia configuration as a ConfigParser instance

    Attributes:
    -----------

    config_file (str): absolute path to the loaded configuration file

    conf (ConfigParser): the loaded configuration

    """
    @staticmethod
    def default_config_file():
        """Return the default abkhazia configuation file

        Look for 'abkhazia.cfg' from pkg_resources, if not found, look
        for __file__/../abkhazia.cfg, else raise a RuntimeError.

        """
        try:
            return pkg.resource_filename(
                pkg.Requirement.parse('abkhazia'), 'abkhazia/abkhazia.cfg')
        except pkg.DistributionNotFound:
            config_file = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                '..', 'abkhazia.cfg')

            if not os.path.isfile(config_file):
                raise RuntimeError(
                    'abkhazia configuration file not found {}'
                    .format(config_file))

            return config_file

    def __init__(self, config_file=None):
        """Load the abkhazia configuration from a given file

        If no `config_file` provided, load the default abkhazia
        configuration file

        """
        if config_file is None:
            config_file = self.default_config_file()
        self.config_file = os.path.abspath(config_file)

        self.conf = ConfigParser.ConfigParser()
        self.conf.readfp(open(self.config_file, 'r'))


# by defining config at module level, we ensure the configuration file
# is loaded once and only once, the first time this module is imported
config = AbkhaziaConfig().conf
