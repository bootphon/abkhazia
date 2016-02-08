"""Provides some misc functions usefull in corpus preparation

@author: Mathieu Bernard

"""

import argparse
import codecs
import os
import re
import shlex
import subprocess
import textwrap

# TODO should be fixed during installation and not relative to __file__
ABKHAZIA_ROOT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../..'))
"""The absolute to the abkhazia installation directory"""


# TODO should be fixed during installation and not relative to ABKHAZIA_ROOT_DIR
KALDI_ROOT_DIR = os.path.abspath(
    os.path.join(ABKHAZIA_ROOT_DIR, '../kaldi'))
"""The absolute to the abkhazia installation directory"""


# TODO should go in a config file
DEFAULT_OUTPUT_DIR = os.path.join(ABKHAZIA_ROOT_DIR, 'corpora')
"""The default output directory for prepared corpora"""


def open_utf8(filename, mode='rb'):
    """Open a file encoded in UTF-8 and return its handler"""
    return codecs.open(filename, mode=mode, encoding='UTF-8')


def list_directory(directory, abspath=False):
    """Return os.listdir(directory) with .DS_Store filtered out"""
    lsd = [e for e in os.listdir(directory) if e != '.DS_Store']
    if abspath:
        lsd = [os.path.abspath(os.path.join(directory, e)) for e in lsd]
    return lsd


def list_files_with_extension(directory, extension):
    """Return all files of given extension in directory hierarchy

    The files are returned in a list with a path relative to
    'directory'

    """
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

    This method lies on the 'flac --decode' system command. Raises an
    OSError if the command 'flac' is not found on the system.

    """
    try:
        subprocess.check_output(shlex.split('which flac'))
    except:
        raise OSError('flac is not installed on your system')

    command = 'flac --decode -s -f {} -o {}'.format(flac, wav)
    subprocess.call(shlex.split(command))


def sph2wav(sph, wav):
    """Convert a sph file to the wav format

    'sph' must be an existing sph file
    'wav' if the filename of the created file

    sph2pipe is required for converting sph to wav. One way to get it
    is to install kaldi, then sph2pipe can be found in:
    /path/to/kaldi/tools/sph2pipe_v2.5/sph2pipe

    Else sph2pipe can be freely downloaded at
    https://www.ldc.upenn.edu/sites/www.ldc.upenn.edu/files/ctools/sph2pipe_v2.5.tar.gz

    """
    sph2pipe = os.path.join(KALDI_ROOT_DIR, 'tools/sph2pipe_v2.5/sph2pipe')
    if not os.path.isfile(sph2pipe):
        raise OSError('sph2pipe not found on your system')

    command = sph2pipe + ' -f wav {0} {1}'.format(sph, wav)
    subprocess.call(shlex.split(command))


def shn2wav(shn, wav):
    """Convert a shn file to the wav format

    'shn' must be an existing sph file
    'wav' if the filename of the created file

    sox and shorten commands are required

    shorten is available at
    http://etree.org/shnutils/shorten/dist/src/shorten-3.6.1.tar.gz

    sox is available at http://sox.sourceforge.net/ or in repositories
    of most Linux distribution (sudo apt-get install sox)

    """
    for cmd in ['shorten', 'sox']:
        try:
            subprocess.check_output(shlex.split('which {}'.format(cmd)))
        except:
            raise OSError('{} is not installed on your system'.format(cmd))

    tmp = shn + '.tmp'
    command1 = 'shorten -x {} {}'.format(shn, tmp)
    command2 = ('sox -t raw -r 16000 -e signed-integer -b 16 {} -t wav {}'
                .format(tmp, wav))

    for cmd in [command1, command2]:
        subprocess.call(shlex.split(cmd))

    try:
        os.remove(tmp)
    except os.error:
        pass


def default_argument_parser(name, description):
    """Return a default argument parser for corpus preparation"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(description))

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='display more messages to stdout '
                        '(this can be a lot)')

    parser.add_argument('-o', '--output-dir', default=None,
                        help='root directory of the prepared corpus, '
                        'if not specified use {}'
                        .format(os.path.join(DEFAULT_OUTPUT_DIR, name)))

    # parser.add_argument('-w', '--overwrite', action='store_true',
    #                     help='delete any existing content on OUTPUT_DIR, '
    #                     'whithout this option the program fails if '
    #                     'OUTPUT_DIR already exists')

    parser.add_argument('--no-validation', action='store_true',
                        help='disable the corpus validation step')

    parser.add_argument('input_dir',
                        help='root directory of the raw corpus distribution, '
                        'must be an existing directory on the filesystem')

    return parser


def main(preparator, description, argparser=default_argument_parser):
    """A main function common to all the corpora preparators

    This function basically does these successive steps:
    - parse the command line arguments
    - initialize the preparator of the specified corpus
    - prepare the corpus (convert it to the abkhazia format)
    - validate the prepared corpus if asked

    """
    try:
        args = argparser(preparator.name, description).parse_args()

        corpus_prep = preparator(
            args.input_dir, args.output_dir, args.verbose)

        corpus_prep.prepare()

        if not args.no_validation:
            corpus_prep.validate()
    except Exception as err:
        print('fatal error: {}'.format(err))
