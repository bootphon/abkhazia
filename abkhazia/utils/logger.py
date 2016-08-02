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
"""Utility for logging to stdout and an optional log file.

This uses the 'logging' module from Python standard library. In the
'logging module', a 'level' is associated to each message. The
possible levels are:

    CRITICAL, ERROR, WARNING, INFO, DEBUG or NOTSET.

This module implements the following behavior:

  - NOTSET messages are ignored
  - all other messages are logged to the specified file
  - if verbose option is set to True, all messages are also printed to
    sys.stdout, if verbose is False, the DEBUG message are not printed

The log file is UTF-8 encoded.

The logs are postprocessed to have a nice log formatting from Kaldi
logs (stripping messages, deleting empty ones, etc.)

"""

import logging
import os
import sys


class LevelFilter(logging.Filter):
    """A utility class to filter out undesirated levels from log output"""
    def __init__(self, passlevels):
        super(LevelFilter, self).__init__()
        self.passlevels = passlevels

    def filter(self, record):
        return record.levelno in self.passlevels


class WhitespaceRemovingFormatter(logging.Formatter):
    """Strip log messages

    Kaldi logs are reported to the abkhazia logger, because they
    include trailing \n, we want to remove that from the messages (ie
    strip them) by defining a custom formatter. From
    https://stackoverflow.com/questions/17931426

    """
    def format(self, record):
        try:
            record.msg = record.msg.strip()
        except AttributeError:
            pass
        return super(WhitespaceRemovingFormatter, self).format(record)


class NoEmptyMessageFilter(logging.Filter):
    """Inhibit empty log messages

    kaldi also generates empty lines, undesirable in a logging framework
    where they generate empty message, so we filter out empty message
    here. From https://stackoverflow.com/questions/879732

    """
    def filter(self, record):
        return len(record.getMessage().strip())


class NoLocalSubdirNotFound(logging.Filter):
    """Inhibit an unrelevant warning from Kaldi

    Kaldi scripts complains about a missing 'local' subdirectory we
    don't rely on, so here we inhibit the concerned log messages

    """
    def filter(self, record):
        return "'local' subdirectory not found." not in record.getMessage()


def get_log(log_file=os.devnull, verbose=False, header_in_stdout=False):
    """Return a configured logger

    Parameters:
    -----------

    log_file (filename): log file to write, default is to not write
        any file

    verbose (bool): if True, send the DEBUG messages to stdout,
        default is False

    header_in_stdout (bool): if True, format the stdout messages as
        "time - level - message", if False display only "message"
        (default is False)

    """
    log = logging.getLogger()
    log.addFilter(NoEmptyMessageFilter())
    log.addFilter(NoLocalSubdirNotFound())
    log.setLevel(logging.DEBUG)

    # delete any existing handler before reconfiguring
    log.handlers = []

    # check if the target dircetory exists, create it if needed
    _dir = os.path.dirname(log_file)
    if not os.path.isdir(_dir) and _dir:
        os.makedirs(_dir)

    # log to dedicated file
    file_handler = logging.FileHandler(log_file, mode='w', encoding="UTF-8")
    formatter = WhitespaceRemovingFormatter(
        '%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    log_filter = LevelFilter(
        [logging.DEBUG, logging.INFO,
         logging.WARNING, logging.ERROR, logging.CRITICAL])
    file_handler.addFilter(log_filter)
    log.addHandler(file_handler)

    # log to standard output
    std_handler = logging.StreamHandler(sys.stdout)
    formatter = WhitespaceRemovingFormatter(
        '%(asctime)s - %(levelname)s - %(message)s'
        if header_in_stdout else '%(message)s')
    std_handler.setFormatter(formatter)
    std_handler.setLevel(logging.DEBUG)

    level_list = [
        logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]
    if verbose:
        level_list = [logging.DEBUG] + level_list

    log_filter = LevelFilter(level_list)
    std_handler.addFilter(log_filter)
    log.addHandler(std_handler)

    return log


def reopen_files(log, mode='a+'):
    """Close and reopen all file handlers in `log`"""
    for h in log.handlers:
        if isinstance(h, logging.FileHandler):
            h.acquire()
            h.stream.close()
            h.stream = open(h.baseFilename, mode)
            h.release()


def null_logger():
    """Return a logger going to nowhere, disable logging"""
    log = logging.getLogger()
    log.addHandler(logging.NullHandler())
    return log
