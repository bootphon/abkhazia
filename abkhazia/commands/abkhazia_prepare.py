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
"""Implementation of the 'abkhazia prepare' command"""

import argparse
import os
import shutil
import textwrap

import abkhazia.utils as utils
from abkhazia.commands.abstract_command import AbstractCommand

# import all the corpora preparators
from abkhazia.corpus.prepare import (
    AICPreparator,
    BuckeyePreparator,
    ChildesPreparator,
    CSJPreparator,
    LibriSpeechPreparator,
    XitsongaPreparator,
    WolofPreparator,
    AbstractGlobalPhonePreparator, MandarinPreparator, VietnamesePreparator,
    JapanesePreparator,
    WallStreetJournalPreparator, JournalistReadPreparator,
    JournalistSpontaneousPreparator, MainReadPreparator, SPSCSJPreparator,
    BuckeyeManualPreparator,
    KCSSPreparator)


class AbstractFactory(object):
    """The Factory class runs a corpus preparator from command-line arguments

    A Factory class is dedicated to a single corpus preparator. It
    does the following things: TODO update

    * add_parser(): define and return an argument parser for the preparator
    * init_preparator(): instanciates the preparator and return it
    * run(): wrap the 2 previous functions, called from AbkhaziaPrepare

    """
    preparator = NotImplemented
    """The corpus preparator attached to the factory"""

    @staticmethod
    def format_url(url, sep='\n'):
        """Return a string from the string (or list of strings) 'url'"""
        if isinstance(url, str):
            return url
        else:
            return sep.join(url)

    @classmethod
    def long_description(cls):
        """Return a multiline description of the corpus being prepared"""
        return (
            'abkhazia corpus preparation for the ' +
            cls.preparator.description +
            '\n\ncorpus description:\n' +
            '  ' + cls.format_url(cls.preparator.url, '\n  ') +
            '\n\n' +
            cls.preparator.long_description.replace('    ', '  '))

    @classmethod
    def default_output_dir(cls):
        """Return the default output directory for corpus preparation

        This directory is 'data-directory'/'name', where
        'data-directory' is read from the abkhazia configuration file
        and 'name' is self.name

        """
        return os.path.join(
            utils.config.get('abkhazia', 'data-directory'),
            cls.preparator.name)

    @classmethod
    def add_parser(cls, subparsers):
        """Return a default argument parser for corpus preparation"""
        parser = subparsers.add_parser(cls.preparator.name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.description = textwrap.dedent(cls.long_description())

        group = parser.add_argument_group('directories')

        default_input_dir = cls.preparator.default_input_dir()
        if default_input_dir is None:
            group.add_argument(
                'input_dir', metavar='<input-dir>',
                help='root directory of the raw corpus distribution')
        else:
            group.add_argument(
                '-i', '--input-dir', metavar='<input-dir>',
                default=default_input_dir,
                help='root directory of the raw corpus distribution, '
                'default is %(default)s')

        group.add_argument(
            '-o', '--output-dir', metavar='<output-dir>', default=None,
            help='the prepared corpus is created in '
            '<output-dir>/data, if not specified use {}.'
            .format(cls.default_output_dir()))

        parser.add_argument(
            '-v', '--verbose', action='store_true',
            help='display more messages to stdout')

        parser.add_argument(
            '-f', '--force', action='store_true',
            help='if specified, overwrite the output directory '
            '<output-dir>/data. If not specified but the directory exists, '
            'the program detects desired wav files already present and '
            'do not convert them again.')

        parser.add_argument(
            '-j', '--njobs', type=int, default=utils.default_njobs(),
            metavar='<njobs>',
            help='number of jobs to launch when doing parallel '
            'computations (mainly for wav conversion). '
            'Default is to launch %(default)s jobs.')

        parser.add_argument(
            '--keep-short-utts', action='store_true',
            help='utterances shorter than 0.1 second are removed by defaults, '
            "as they won't be accepted by Kaldi for feature extraction. "
            "Use this option to keep those short utterances in the corpus.")

        if cls.preparator.audio_format == 'wav':
            parser.add_argument(
                '--copy-wavs', action='store_true',
                help='the audio files of this corpus are already in wav. '
                'By default abkhazia will import them as symbolic links, '
                'use this option to force copy')

        return parser

    @classmethod
    def _output_dir(cls, args):
        """Return the preparator output directory <output-dir>/data

        if the --force option have been specified, delete
        <output-dir>/data before returning it.

        """
        output_dir = os.path.join(
            cls.default_output_dir() if args.output_dir is None
            else args.output_dir, 'data')

        if args.force and os.path.exists(output_dir):
            print 'removing {}'.format(output_dir)
            shutil.rmtree(output_dir)

        return output_dir

    @classmethod
    def init_preparator(cls, args):
        """Return an initialized preparator from parsed arguments"""
        return cls.preparator(args.input_dir)

    @classmethod
    def _run_preparator(cls, args, preparator, output_dir=None):
        output_dir = ((
            cls._output_dir(args) if args.output_dir is None
            else os.path.abspath(os.path.join(args.output_dir, 'data')))
                      if output_dir is None else output_dir)
        preparator.log = utils.logger.get_log(
            os.path.join(output_dir, 'data_preparation.log'), args.verbose)

        # initialize corpus from raw with it's preparator
        corpus = preparator.prepare(
            os.path.join(output_dir, 'wavs'),
            keep_short_utts=args.keep_short_utts)
        corpus.log = utils.logger.get_log(
            os.path.join(output_dir, 'data_validation.log'), args.verbose)

        # raise if the corpus is not in correct abkhazia
        # format. Redirect the log to the preparator logger
        corpus.validate(njobs=args.njobs)

        # save the corpus to the output directory
        corpus.save(output_dir, no_wavs=True)

    @classmethod
    def run(cls, args):
        """Initialize, validate and save a corpus from command line args"""
        cls._run_preparator(args, cls.init_preparator(args))


class AbstractFactoryWithCMU(AbstractFactory):
    """Preparation for corpora relying of the CMU dictionary"""
    @classmethod
    def add_parser(cls, subparsers):
        parser = super(AbstractFactoryWithCMU, cls).add_parser(subparsers)

        parser.add_argument(
            '--cmu-dict', default=None, metavar='<cmu-dict>',
            help='the CMU dictionary file to use for lexicon generation. '
            'If not specified use {}'.format(cls.preparator.default_cmu_dict))

        return parser

    @classmethod
    def init_preparator(cls, args):
        return cls.preparator(
            args.input_dir, cmu_dict=args.cmu_dict)


class BuckeyeFactory(AbstractFactory):
    preparator = BuckeyePreparator


class BuckeyeManualFactory(AbstractFactory):
    preparator = BuckeyeManualPreparator


class XitsongaFactory(AbstractFactory):
    preparator = XitsongaPreparator


class CSJFactory(AbstractFactory):
    preparator = CSJPreparator

    @classmethod
    def add_parser(cls, subparsers):
        parser = super(CSJFactory, cls).add_parser(subparsers)

        parser.add_argument(
                '--clusters', action='store_true',
                help='enable if you want to keep clusters (e.g. c+y'
                'as c+y). Else, c+y will be put as (c,y)')
        parser.add_argument(
                '--core', action='store_true',
                help='enable if you want to only treat the core '
                'files in your directory. If not enabled, all the '
                'files in your directory will be treated using the '
                'non-core recipe')

    @classmethod
    def init_preparator(cls, args):
        return cls.preparator(
            args.input_dir,
            copy_wavs=True,
            clusters=args.clusters,
            treat_core=args.core)


class ChildesFactory(AbstractFactory):
    preparator = ChildesPreparator


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
    def add_parser(cls, subparsers):
        selection_descr = ', '.join(
            [str(i+1) + ' is ' + cls.selection[i]
             for i in range(len(cls.selection))])

        parser = super(LibriSpeechFactory, cls).add_parser(subparsers)

        parser.add_argument(
            '-s', '--selection', default=None,
            metavar='<selection>', type=int,
            help='the subpart of LibriSpeech to prepare. If not specified, '
            'prepare the entire corpus. Choose <selection> in {}. ('
            .format(range(1, len(cls.selection)+1)) + selection_descr + ')')

        parser.add_argument(
            '-l', '--librispeech-dict', default=None,
            help='the librispeech-lexicon.txt file at the root '
            'of the LibriSpeech distribution. '
            'If not specified, guess it from <input-dir>')

        return parser

    @classmethod
    def _selection(cls, args):
        return (None if args.selection is None
                else cls.selection[args.selection-1])

    @classmethod
    def _output_dir(cls, args):
        _dir = super(LibriSpeechFactory, cls)._output_dir(args)
        if args.output_dir is None:
            # remove '/data' from path
            d = os.path.dirname(_dir)
            # append selection name to path
            d = d if args.selection is None else d + '-' + cls._selection(args)
            # reappend '/data'
            return os.path.join(d, 'data')
        else:
            return (_dir if args.selection is None
                    else _dir + '-' + cls._selection(args))

    @classmethod
    def init_preparator(cls, args):
        return cls.preparator(
            args.input_dir,
            selection=cls._selection(args),
            cmu_dict=args.cmu_dict,
            librispeech_dict=args.librispeech_dict)


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
    def add_parser(cls, subparsers):
        selection_descr = ', '.join([
            str(i+1) + ' is ' + cls.selection[i][0]
            for i in range(len(cls.selection))])

        parser = super(WallStreetJournalFactory, cls).add_parser(subparsers)

        parser.add_argument(
            '-s', '--selection', default=None,
            metavar='<selection>', type=int,
            choices=range(1, len(cls.selection)+1),
            help='the subpart of WSJ to prepare. If not specified, '
            'prepare the entire corpus. Choose <selection> in {} ('
            .format(range(1, len(cls.selection)+1)) + selection_descr + '). '
            'If <selection> is specified but not <output-dir>, the selection '
            'name will be appended to the default output directory (e.g. for '
            '-s 1 it will be .../wsj-journalist-read instead of .../wsj).')

        return parser

    @classmethod
    def _output_dir(cls, args):
        _dir = super(WallStreetJournalFactory, cls)._output_dir(args)
        if args.output_dir is None:
            # remove '/data' from path
            d = os.path.dirname(_dir)
            # append selection name to path
            d = (d if args.selection is None
                 else d + '-' + cls.selection[args.selection-1][0])
            # reappend '/data'
            return os.path.join(d, 'data')
        else:
            return (_dir if args.selection is None
                    else _dir + '-' + cls._selection(args))

    @classmethod
    def init_preparator(cls, args):
        # select the preparator
        preparator = (cls.preparator if args.selection is None
                      else cls.selection[args.selection-1][1])
        return preparator(args.input_dir, cmu_dict=args.cmu_dict)


class GlobalPhoneFactory(AbstractFactory):
    preparator = AbstractGlobalPhonePreparator

    # all the supported languages mapped to their preparators
    preparators = {
        'japanese': JapanesePreparator,
        'mandarin': MandarinPreparator,
        'vietnamese': VietnamesePreparator
    }

    @classmethod
    def add_parser(cls, subparsers):
        """Overload of the AbstractPreparator.parser for GlobalPhone"""
        # add a language selection option to the arguments parser
        parser = super(GlobalPhoneFactory, cls).add_parser(subparsers)

        parser.add_argument(
            '-l', '--language', nargs='+', metavar='<language>',
            default=cls.preparators.keys(),
            choices=cls.preparators.keys(),
            help='specify the languages to prepare in {}, '
            'if this option is not specified prepare all the '
            'supported languages. '.format(cls.preparators.keys()) +
            'Actually only Vietnamese and Mandarin are supported '
            'by abkhazia.')
        parser.add_argument(
            '--clusters', action='store_true',
            help='If language is japanese, setting clusters to true'
            'forces the preparator to keep phonemes such as "cy" '
            ' "zy" etc.. together. If --clusters is not enabled'
            'such phonemes will be seperated, e.g. cy -> c,y .')

        return parser

    @classmethod
    def init_preparator(cls, args):
        preps = []
        for lang in args.language:
            prep = cls.preparators[lang]
            if lang == 'japanese':
                p = prep(args.input_dir, args.clusters)
            else:
                p = prep(args.input_dir)
            p.njobs = args.njobs
            preps.append(p)
        return preps

    @classmethod
    def _run_preparator(cls, args, preparator):
        lang = preparator.language.lower()
        d = os.path.join(os.path.dirname(cls._output_dir(args)), lang, 'data')
        preparator.log = utils.logger.get_log(
            os.path.join(d, 'data_preparation.log'), args.verbose)
        super(GlobalPhoneFactory, cls)._run_preparator(args, preparator, d)

    @classmethod
    def run(cls, args):
        for prep in cls.init_preparator(args):
            cls._run_preparator(args, prep)


class WolofFactory(AbstractFactory):
    preparator = WolofPreparator


class SPSCSJFactory(AbstractFactory):
    preparator = SPSCSJPreparator


class KCSSFactory(AbstractFactory):
    preparator = KCSSPreparator

    @classmethod
    def add_parser(cls, subparsers):
        parser = super(KCSSFactory, cls).add_parser(subparsers)

        parser.add_argument(
            '-l', '--level', choices=['pronunciation', 'orthographic'],
            default='pronunciation',
            help='prepare the corpus from data annotated at pronunciation '
            'level (default) or orthographic level')

        parser.add_argument(
            '--no-alignment', action='store_true',
            help='Do not extract the time alignment from the orginal corpus')

        return parser

    @classmethod
    def init_preparator(cls, args):
        return cls.preparator(
            args.input_dir,
            trs_level=args.level,
            extract_alignment=not args.no_alignment,
            log=utils.logger.get_log(verbose=args.verbose))

    @classmethod
    def _run_preparator(cls, args, preparator, output_dir=None):
        output_dir = ((
            cls._output_dir(args) if args.output_dir is None
            else os.path.abspath(os.path.join(args.output_dir, 'data')))
                      if output_dir is None else output_dir)
        preparator.log = utils.logger.get_log(
            os.path.join(output_dir, 'data_preparation.log'), args.verbose)

        # initialize corpus from raw with it's preparator
        corpus = preparator.prepare(
            os.path.join(output_dir, 'wavs'),
            keep_short_utts=args.keep_short_utts)
        corpus.log = utils.logger.get_log(
            os.path.join(output_dir, 'data_validation.log'), args.verbose)

        # raise if the corpus is not in correct abkhazia
        # format. Redirect the log to the preparator logger
        corpus.validate(njobs=args.njobs)

        # save the corpus to the output directory
        corpus.save(output_dir, no_wavs=True)

        # save the alignment
        if not args.no_alignment:
            alignment_file = os.path.join(output_dir, 'alignment.txt')
            utils.open_utf8(alignment_file, 'w').write(
                '\n'.join(
                    '{} {}'.format(k, ' '.join(str(v) for v in vv))
                    for k, v in sorted(preparator.alignment.items())
                    for vv in v)
                + '\n')


class AbkhaziaPrepare(AbstractCommand):
    name = 'prepare'
    description = 'prepare a speech corpus for use with abkhazia'

    supported_corpora = {c.preparator.name: c for c in (
        AICFactory,
        BuckeyeFactory,
        ChildesFactory,
        CSJFactory,
        GlobalPhoneFactory,
        LibriSpeechFactory,
        WallStreetJournalFactory,
        WolofFactory,
        XitsongaFactory,
        SPSCSJFactory,
        BuckeyeManualFactory,
        KCSSFactory
    )}

    @classmethod
    def describe_corpora(cls):
        """Return a list of strings describing the supported corpora"""
        return ['{} - {}'.format(
            # librispeech is the longest corpus name so the desired
            # key length is len('librispeech ') == 11
            key + ' '*(11 - len(key)),
            value.preparator.description)
                for key, value in sorted(cls.supported_corpora.iteritems())]

    @classmethod
    def add_parser(cls, subparsers):
        # get basic parser init from AbstractCommand
        parser = super(AbkhaziaPrepare, cls).add_parser(subparsers)

        # setup custom help formatter and description
        parser.formatter_class = argparse.RawTextHelpFormatter
        parser.description = textwrap.dedent(
            cls.description + '\n' +
            "type 'abkhazia prepare <corpus> --help' for help " +
            'on a specific corpus\n\n')

        # register the subparsers belonging to each supported corpus
        subparsers = parser.add_subparsers(
            metavar='<corpus>', dest='corpus',
            help=textwrap.dedent('supported corpora are:\n' +
                                 '\n'.join(cls.describe_corpora())))
        for corpus in cls.supported_corpora.itervalues():
            corpus.add_parser(subparsers)

    @classmethod
    def run(cls, args):
        # delegation to the run() method of the chosen corpus factory
        cls.supported_corpora[args.corpus].run(args)
