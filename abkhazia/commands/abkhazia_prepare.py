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
"""Implementation of the 'abkhazia prepare' command"""

import argparse
import sys
import textwrap

from abkhazia.prepare.aic_preparator import AICPreparator
from abkhazia.prepare.buckeye_preparator import BuckeyePreparator
from abkhazia.prepare.csj_preparator import CSJPreparator
from abkhazia.prepare.librispeech_preparator import LibriSpeechPreparator
from abkhazia.prepare.xitsonga_preparator import XitsongaPreparator

from abkhazia.prepare.globalphone_abstract_preparator import (
    AbstractGlobalPhonePreparator)
from abkhazia.prepare.globalphone_mandarin_preparator import (
    MandarinPreparator)
from abkhazia.prepare.globalphone_vietnamese_preparator import (
    VietnamesePreparator)

from abkhazia.prepare.wsj_preparator import (
    WallStreetJournalPreparator,
    JournalistReadPreparator,
    JournalistSpontaneousPreparator,
    MainReadPreparator)

from abkhazia.prepare import validation


class AbstractFactory(object):
    """The Factory class runs a corpus preparator from command-line arguments

    A Factory class is dedicated to a single corpus preparator. It
    does the following things:

    * parser(): define and return an argument parser for the preparator
    * init_preparator(): instanciates the preparator and return it
    * run(): wrap the 2 previous functions, called from AbkhaziaPrepare

    """
    preparator = NotImplemented
    """The corpus preparator attached to the factory"""

    @classmethod
    def parser(cls):
        """Return a default argument parser for corpus preparation"""
        prog = 'abkhazia prepare {}'.format(cls.preparator.name.lower())

        parser = argparse.ArgumentParser(
            prog=prog,
            usage=('%(prog)s <input-dir> [--output-dir OUTPUT_DIR]\n'
                   + ' '*(len(prog)+8)
                   + ('\n' + ' '*(len(prog)+8)).join([
                       '[--help] [--verbose] [--njobs NJOBS]',
                       '[--no-validation|--only-validation]'])),
            description=cls.preparator.description)

        group = parser.add_argument_group('directories')

        group.add_argument(
            'input_dir', metavar='input-dir',
            help='root directory of the raw corpus distribution')

        group.add_argument(
            '-o', '--output-dir',
            default=None,
            help='output directory of the prepared corpus, '
            'if not specified use {}'
            .format(cls.preparator.default_output_dir()))

        parser.add_argument(
            '-v', '--verbose', action='store_true',
            help='display more messages to stdout')

        parser.add_argument(
            '-j', '--njobs', type=int, default=4,
            help='number of jobs to launch when doing parallel '
            'computations (mainly for wav conversion). '
            'Default is to launch %(default)s jobs.')

        group = parser.add_argument_group('validation options')
        group = group.add_mutually_exclusive_group()
        group.add_argument(
            '--no-validation', action='store_true',
            help='disable the corpus validation step (do only preparation)')
        group.add_argument(
            '--only-validation', action='store_true',
            help='disable the corpus preparation step (do only validation)')

        if cls.preparator.audio_format == 'wav':
            parser.add_argument(
                '--copy-wavs', action='store_true',
                help='the audio files of this corpus are already in wav. '
                'By default abkhazia will import them as symbolic links, '
                'use this option to force copy')

            parser.usage += ' [--copy-wavs]'

        return parser

    @classmethod
    def init_preparator(cls, args):
        """Return an initialized preparator from parsed arguments"""
        if cls.preparator.audio_format == 'wav':
            prep = cls.preparator(args.input_dir, args.output_dir,
                                  args.verbose, args.njobs, args.copy_wavs)
        else:
            prep = cls.preparator(args.input_dir, args.output_dir,
                                  args.verbose, args.njobs)
        return prep

    @classmethod
    def run(cls):
        """Initialize and run a preparator from command line arguments"""
        args = cls.parser().parse_args(sys.argv[3:])

        if not args.only_validation:
            cls.init_preparator(args).prepare()

        if not args.no_validation:
            output_dir = (cls.preparator.default_output_dir()
                          if args.output_dir is None
                          else args.output_dir)
            validation.validate(output_dir, args.verbose)


class AbstractFactoryWithCMU(AbstractFactory):
    @classmethod
    def parser(cls):
        parser = super(AbstractFactoryWithCMU, cls).parser()
        parser.usage += ('\n' + ' '*(len(parser.prog)+8)
                         + '[--cmu-dict CMU_DICT]')

        parser.add_argument(
            '--cmu-dict', default=None,
            help='the CMU dictionary file to use for lexicon generation. '
            'If not specified use {}'.format(cls.preparator.default_cmu_dict))

        return parser

    @classmethod
    def init_preparator(cls, args):
        return cls.preparator(
            args.input_dir, args.cmu_dict,
            args.output_dir, args.verbose, args.njobs)


class BuckeyeFactory(AbstractFactory):
    preparator = BuckeyePreparator

class XitsongaFactory(AbstractFactory):
    preparator = XitsongaPreparator

class CSJFactory(AbstractFactory):
    preparator = CSJPreparator

class AICFactory(AbstractFactoryWithCMU):
    preparator = AICPreparator

class LibriSpeechFactory(AbstractFactoryWithCMU):
    preparator = LibriSpeechPreparator

    # list of the LibriSpeech subcorpora. TODO this is actually
    # hard-coded to present a selection on --help. See if we can get
    # the selection at runtime by scanning input_dir...
    selection = ['dev-clean', 'dev-other',
                 'test-clean', 'test-other',
                 'train-clean-100', 'train-clean-360']

    @classmethod
    def parser(cls):
        selection_descr = ', '.join(
            [str(i+1) + ' is ' + cls.selection[i]
             for i in range(len(cls.selection))])

        parser = super(LibriSpeechFactory, cls).parser()
        parser.usage += (' [--librispeech-dict LIBRISPEECH_DICT]\n'
                         + ' '*(len(parser.prog)+8)
                         + '[--selection SELECTION]')

        parser.add_argument(
            '-s', '--selection', default=None,
            metavar='SELECTION', type=int,
            help='the subpart of LibriSpeech to prepare. If not specified, '
            'prepare the entire corpus. Choose SELECTION in {}. ('
            .format(range(1, len(cls.selection)+1)) + selection_descr + ')')

        parser.add_argument(
            '-l', '--librispeech-dict', default=None,
            help='the librispeech-lexicon.txt file at the root '
            'of the LibriSpeech distribution. '
            'If not specified, guess it from INPUT_DIR')

        return parser

    @classmethod
    def init_preparator(cls, args):
        selection = (None if args.selection is None
                     else cls.selection[args.selection-1])

        return cls.preparator(
            args.input_dir, selection,
            args.cmu_dict, args.librispeech_dict,
            args.output_dir, args.verbose, args.njobs)

class WallStreetJournalFactory(AbstractFactoryWithCMU):
    """Instanciate and run one of the WSJ preparators from input arguments"""
    preparator = WallStreetJournalPreparator

    # mapping of the three WSJ specialized preparators
    selection = [
        ('journalist-read', JournalistReadPreparator),
        ('journalist-spontaneous', JournalistSpontaneousPreparator),
        ('main-read', MainReadPreparator)
    ]

    @classmethod
    def parser(cls):
        selection_descr = ', '.join([
            str(i+1) + ' is ' + cls.selection[i][0]
            for i in range(len(cls.selection))])

        parser = super(WallStreetJournalFactory, cls).parser()
        parser.usage += ' [--selection SELECTION]'

        parser.add_argument(
            '-s', '--selection', default=None,
            metavar='SELECTION', type=int,
            choices=range(1, len(cls.selection)+1),
            help='the subpart of WSJ to prepare. If not specified, '
            'prepare the entire corpus. Choose SELECTION in {}. ('
            .format(range(1, len(cls.selection)+1)) + selection_descr + ')')

        return parser

    @classmethod
    def init_preparator(cls, args):
        # select the preparator
        preparator = (cls.preparator if args.selection is None
                      else cls.selection[args.selection-1][1])

        return preparator(
            args.input_dir, args.cmu_dict,
            args.output_dir, args.verbose, args.njobs)

class GlobalPhoneFactory(AbstractFactory):
    preparator = AbstractGlobalPhonePreparator

    # all the supported languages mapped to their preparators
    preparators = {
        'Mandarin': MandarinPreparator,
        'Vietnamese': VietnamesePreparator
    }

    @classmethod
    def parser(cls):
        """Overload of the AbstractPreparator.parser for GlobalPhone"""
        # add a language selection option to the arguments parser
        parser = super(GlobalPhoneFactory, cls).parser()
        parser.usage += '\n' + ' '*36 + '[--language {Mandarin,Vietnamese}]'

        parser.add_argument(
            '-l', '--language', nargs='+', metavar='LANGUAGE',
            default=cls.preparators.keys(),
            choices=cls.preparators.keys(),
            help='specify the languages to prepare in {}, '
            'if this option is not specified prepare all the '
            'supported languages'.format(cls.preparators.keys()))

        return parser

    @classmethod
    def init_preparator(cls, args):
        return (cls.preparators[language](
            args.input_dir, args.output_dir, args.verbose, args.njobs)
                for language in args.language)

    @classmethod
    def run(cls):
        args = cls.parser().parse_args(sys.argv[3:])

        for prep in cls.init_preparator(args):
            if not args.only_validation:
                prep.prepare()

            if not args.no_validation:
                output_dir = (prep.default_output_dir()
                              if args.output_dir is None
                              else args.output_dir)

                validation.validate(output_dir, args.verbose)


class AbkhaziaPrepare(object):
    name = 'prepare'
    description = 'Prepare a corpus for use with abkhazia'

    supported_corpora = dict((n, c) for n, c in (
        ('aic', AICFactory),
        ('buckeye', BuckeyeFactory),
        ('csj', CSJFactory),
        ('globalphone', GlobalPhoneFactory),
        ('librispeech', LibriSpeechFactory),
        ('wsj', WallStreetJournalFactory),
        ('xitsonga', XitsongaFactory)
    ))

    @staticmethod
    def format_url(url, sep='\n'):
        """Return a string from the string (or list of strings) 'url'"""
        if isinstance(url, str):
            return sep + url
        else:
            return sep + sep.join(url)

    def describe_corpora(self):
        """Return a list of strings describing the supported corpora"""
        return ['{} - {}{}'.format(
            # desired key length is len('librispeech ') == 12
            key + ' '*(12 - len(key)),
            value.preparator.description,
            self.format_url(value.preparator.url, '\n\t\t   '))
                for key, value in sorted(self.supported_corpora.iteritems())]

    def corpus_parser(self):
        """Return a parser dedicated to the corpus parameter"""
        long_description = (
            self.description + '\n'
            + "type 'abkhazia prepare <corpus> --help' for help "
            + 'on a specific corpus\n\n'
            + 'supported corpora are:\n    '
            + '\n    '.join(self.describe_corpora()))

        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            usage='abkhazia prepare <corpus> [--help] [<args>]',
            description=textwrap.dedent(long_description))

        parser.add_argument(
            'corpus', metavar='corpus', help='the speech corpus to prepare')

        return parser

    def __init__(self):
        # init the corpus parser
        parser = self.corpus_parser()

        # parse the corpus name from the 3rd command line argument
        try:
            corpus = parser.parse_args([sys.argv[2]]).corpus
        except IndexError:
            print 'You must specify a corpus'
            parser.print_help()
            sys.exit(1)

        # retrieve the requested factory from the corpus name
        try:
            factory = self.supported_corpora[corpus]
        except KeyError:
            print "The corpus '{}' is not supported".format(corpus)
            parser.print_help()
            sys.exit(1)

        # init the preparator from arguments and run it
        factory.run()
