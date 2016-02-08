# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 00:17:47 2015

@author: Thomas Schatz
"""

"""Utility for logging to a specified file.

This uses the 'logging' module from Python standard library. In the
'logging module', a 'level' is associated to each message. The
possible levels are:

    CRITICAL, ERROR, WARNING, INFO, DEBUG or NOTSET.

The log2file module currently implements the following behavior:
    - NOTSET messages are ignored
    - INFO messages are printed to sys.stdout
    - all other messages are logged to the specified file
    - if verbose option is set to True, all messages are also printed
      to sys.stdout

The log file is UTF-8 encoded.

"""

import logging
import sys


class LevelFilter(logging.Filter):
    def __init__(self, passlevels):
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
    log_handler = logging.FileHandler(log_file, mode='w', encoding="UTF-8")
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_handler.setFormatter(formatter)
    log_handler.setLevel(logging.DEBUG)

    log_filter = LevelFilter([logging.DEBUG, logging.INFO,
                              logging.WARNING, logging.ERROR,
                              logging.CRITICAL])
    log_handler.addFilter(log_filter)
    log.addHandler(log_handler)

    # log to standard output
    log_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(message)s')
    log_handler.setFormatter(formatter)
    log_handler.setLevel(logging.DEBUG)

    if verbose:
        log_filter = LevelFilter([logging.DEBUG, logging.INFO,
                                  logging.WARNING, logging.ERROR,
                                  logging.CRITICAL])
    else:
        log_filter = LevelFilter([logging.INFO])
    log_handler.addFilter(log_filter)
    log.addHandler(log_handler)

    return log
