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
"""Implementation of the 'abkhazia acoustic' command"""

import argparse
import os
import textwrap

import abkhazia.acoustic as acoustic
import abkhazia.utils as utils
import abkhazia.kaldi as kaldi

from abkhazia.commands.abstract_command import AbstractKaldiCommand
from abkhazia.corpus import Corpus


class _AmBase(AbstractKaldiCommand):
    # name of subcommand in command-line
    name = NotImplemented

    # one line description of the subcommand
    description = NotImplemented

    # multiline detailed description
    _long_description = NotImplemented

    # linked acoustic model class in abkhazia.models.acoustic
    am_class = NotImplemented

    # because models are successive processings, need to reference the
    # previous step. Must be a tuple (short, long), e.g. ('feats',
    # 'features')
    prev_step = NotImplemented

    @classmethod
    def long_description(cls):
        return textwrap.dedent(cls._long_description)

    @classmethod
    def add_parser(cls, subparsers):
        parser, dir_group = super(_AmBase, cls).add_parser(
            subparsers, name=cls.name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.description = cls.long_description()

        lex = parser.add_argument_group('lexixon parameters')
        lex.add_argument(
            '-s', '--silence-probability', default=0.5,
            metavar='<float>', type=float,
            help='usually 0.0 or 0.5, default is %(default)s')

        lex.add_argument(
            '-w', '--word-position-dependent', action='store_true',
            help='''If specified the produced language model is destined to be used
            with an acoustic model trained with word position
            dependent variants of the phones.''')

        lex.add_argument(
            '-l', '--lang-level', default='word',
            help="compute the AM either at phone-level or word-level, "
            "default is '%(default)s'",
            metavar='<phone|word>', choices=['phone', 'word'])

        dir_group.add_argument(
            '-f', '--features', metavar='<feats-dir>', default=None,
            help='')

        if cls.prev_step:
            # if not monophone, add a --input-dir option to specify
            # input acoustic model
            dir_group.add_argument(
                '-i', '--input-dir',
                metavar='<{}-dir>'.format(cls.prev_step[0]),
                help='''the input directory, data is read
                from <{0}-dir>/{1}, if not specified use <{0}-dir>=<corpus>.'''
                .format(cls.prev_step[0], cls.prev_step[1]))

        # add parameters for Kaldi options
        kaldi_group = parser.add_argument_group('training parameters')
        kaldi.options.add_options(kaldi_group, cls.am_class.options)

        return parser

    @classmethod
    def run(cls, args):
        corpus_dir, output_dir = cls._parse_io_dirs(args)
        log = utils.logger.get_log(
            os.path.join(output_dir, '{}.log'.format(cls.name)),
            verbose=args.verbose)
        corpus = Corpus.load(corpus_dir, validate=args.validate, log=log)

        # get back the features directory TODO use cls._parse_aux_dir
        feats = (os.path.join(os.path.dirname(corpus_dir), 'features')
                 if args.features is None
                 else os.path.abspath(args.features))

        # pack the prepare_lang related arguments
        lang_args = {
            'level': args.lang_level,
            'silence_probability': args.silence_probability,
            'position_dependent_phones': args.word_position_dependent,
            'keep_tmp_dirs': True if args.recipe else False}

        # instanciate and setup the kaldi recipe with standard args
        if cls.am_class is not acoustic.Monophone:
            # get back the input directory
            input_dir = (
                os.path.join(os.path.dirname(corpus_dir),
                             '{}'.format(cls.prev_step[1]))
                if args.input_dir is None
                else os.path.abspath(args.input_dir))

            recipe = cls.am_class(
                corpus, feats, input_dir, output_dir, lang_args, log=log)
        else:  # special case of monophone models
            if args.alignment:
                cls.am_class = acoustic.MonophoneFromAlignment
                recipe = cls.am_class(
                    corpus, feats, output_dir, lang_args,
                    args.alignment, log=log)
            else:
                recipe = cls.am_class(
                    corpus, feats, output_dir, lang_args, log=log)

        recipe.njobs = args.njobs
        if args.recipe:
            recipe.delete_recipe = False

        # setup the model options parsed from command line
        for k, v in vars(args).iteritems():
            try:
                recipe.set_option(k.replace('_', '-'), v)
            except KeyError:
                pass
            except AttributeError:
                pass

        # finally train the acoustic model
        recipe.compute()


class _AmMono(_AmBase):
    name = 'monophone'
    description = 'Monophone HMM-GMM acoustic model'
    am_class = acoustic.Monophone
    prev_step = None  # monophone is built directly on features
    _long_description = '''
        Training a monophone HMM-GMM acoustic model on a corpus, with
        attached features (<feat-dir> option).

        Other training options, such as the number of
        Gaussians or iterations, are specified in the "training
        parameters" section (see below).

        The trained model is wrote in a directory specified by the
        <output-dir> option. It can then feed the "abkhazia align",
        "abkhazia decode" or "abkhazia acoustic triphone" commands.'''

    @classmethod
    def add_parser(cls, subparsers):
        parser = super(_AmMono, cls).add_parser(subparsers)
        parser.add_argument(
            '-a', '--alignment', metavar='<file>', default=None,
            help='Provide a phone alignment (by default it is estimated '
            'during training iterations), when this option is in use, the '
            'option --realign-iterations is ignored')


class _AmTri(_AmBase):
    name = 'triphone'
    description = 'Triphone HMM-GMM acoustic model'
    am_class = acoustic.Triphone
    prev_step = ('mono', 'monophone')
    _long_description = '''
        Training a triphone HMM-GMM acoustic model on a corpus.

        The model is trained on a monophone model, coming from the
        "abkhazia acoustic monophone" command and specified by the
        <mono-dir> option.

        Other training options, such as the number of Gaussians or
        iterations, are specified in the "training parameters" section
        (see below).

        The trained model is wrote in a directory specified by the
        <output-dir> option. It can then feed the "abkhazia align",
        "abkhazia decode" or "abkhazia acoustic triphone-sa"
        commands.'''


class _AmTriSa(_AmBase):
    name = 'triphone-sa'
    description = 'Triphone speaker adaptive HMM-GMM acoustic model'
    am_class = acoustic.TriphoneSpeakerAdaptive
    prev_step = ('tri', 'triphone')
    _long_description = '''
        Training a triphone speaker adaptive HMM-GMM acoustic model on a
        corpus.

        The model is trained on a triphone model, coming from the
        "abkhazia acoustic triphone" command and specified by the
        <tri-dir> option.

        Other training options, such as the number of Gaussians or
        iterations, are specified in the "training parameters" section
        (see below).

        The trained model is wrote in a directory specified by the
        <output-dir> option. It can then feed the "abkhazia align",
        "abkhazia decode" or "abkhazia acoustic triphone-dnn"
        commands.'''


class _AmDnn(_AmBase):
    name = 'nnet'
    description = 'HMM-DNN acoustic model'
    am_class = acoustic.NeuralNetwork
    prev_step = ('am', 'acoustic-model')
    _long_description = '''
        Training a neural netwok with pnorm nonlinearities on a
        corpus.

        The model is trained on top of a previously computed HMM-GMM
        acoustic model, specified by the <am-dir> option.

        The trained model is wrote in a directory specified by the
        <output-dir> option. It can then feed the "abkhazia align" or
        "abkhazia decode" commands.

        See http://kaldi-asr.org/doc/dnn2.html for details on the DNN
        recipe implementation '''


class AbkhaziaAcoustic(object):
    name = 'acoustic'
    description = 'train acoustic models from corpus, features and LM'

    _commands = [_AmMono, _AmTri, _AmTriSa, _AmDnn]

    @classmethod
    def add_parser(cls, subparsers):
        """Return a parser for the 'abkhazia acoustic' command

        Add a subparser and help message for 'monophone', 'triphone',
        'triphone-sa' and 'nnet' subcommands.

        """
        parser = subparsers.add_parser(cls.name)
        parser.formatter_class = argparse.RawTextHelpFormatter
        subparsers = parser.add_subparsers(
            metavar='<command>',
            help='possible commands are:\n' + '\n'.join(
                (' {} - {}'.format(
                    c.name + ' '*(11-len(c.name)), c.description)
                 for c in cls._commands)))

        for command in cls._commands:
            command.add_parser(subparsers)

        return parser
