# -*- coding: utf-8 -*-
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
"""Utility for logging to a specified file.

This uses the 'logging' module from Python standard library. In the
'logging module', a 'level' is associated to each message. The
possible levels are:

    CRITICAL, ERROR, WARNING, INFO, DEBUG or NOTSET.

The log2file module implements the following behavior:

  - NOTSET messages are ignored
  - all other messages are logged to the specified file
  - if verbose option is set to True, all messages are also printed to
    sys.stdout, if verbose is False, the DEBUG message are not printed

The log file is UTF-8 encoded.

"""

import logging
import sys


class LevelFilter(logging.Filter):
    """A utility class to filter out undesirated levels from log output"""
    def __init__(self, passlevels):
        super(LevelFilter, self).__init__()
        self.passlevels = passlevels

    def filter(self, record):
        return record.levelno in self.passlevels


def get_log(log_file, verbose=False):
    """Configure and return a logger instance"""
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)

    # delete any existing handler before reconfiguring
    log.handlers = []

    # log to dedicated file
    file_handler = logging.FileHandler(log_file, mode='w', encoding="UTF-8")
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    log_filter = LevelFilter(
        [logging.DEBUG, logging.INFO,
         logging.WARNING, logging.ERROR, logging.CRITICAL])
    file_handler.addFilter(log_filter)
    log.addHandler(file_handler)

    # log to standard output
    std_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(message)s')
    std_handler.setFormatter(formatter)
    std_handler.setLevel(logging.DEBUG)

    if verbose:
        log_filter = LevelFilter(
            [logging.DEBUG, logging.INFO,
             logging.WARNING, logging.ERROR, logging.CRITICAL])
    else:
        log_filter = LevelFilter(
            [logging.INFO, logging.WARNING,
             logging.ERROR, logging.CRITICAL])
    std_handler.addFilter(log_filter)
    log.addHandler(std_handler)

    return log
