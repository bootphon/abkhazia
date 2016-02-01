"""Provides some misc functions usefull in corpus preparation

@author: Mathieu Bernard

"""

import os
import re
import shlex
import subprocess


# TODO should be fixed during installation and not relative to __file__
ABKHAZIA_ROOT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..'))
"""The absolute to the Abkhazia installation directory"""


# TODO should go in a config file
DEFAULT_OUTPUT_DIR = os.path.join(ABKHAZIA_ROOT_DIR, 'corpora')
"""The default output directory for prepared corpora"""


def list_files_with_extension(directory, extension):
    """Return a list of all files of given extension in directory hierarchy"""
    # the regular expression to match in filenames
    expr = r'(.*)' + extension + '$'

    # build the list of matching files
    matched = []
    for path, _, files in os.walk(directory):
        matched += [os.path.join(path, f) for f in files if re.match(expr, f)]
    return matched


def flac2wav(flac, wav):
    """Convert a flac file to the wav format

    'flac' must be an existing flac file
    'wav' is the filename of the created file

    This method lies on the 'flac --decode' system command

    """
    command = 'flac --decode -f {} -o {}'.format(flac, wav)
    subprocess.call(shlex.split(command))
