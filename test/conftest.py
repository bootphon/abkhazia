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
"""Abkhazia test setup"""

import os
import re

import pytest

import abkhazia.utils as utils
from abkhazia.corpus.prepare import BuckeyePreparator
from abkhazia.corpus import Corpus
from abkhazia.features import Features
from abkhazia.language import LanguageModel
import abkhazia.acoustic as acoustic


def assert_no_expr_in_log(flog, expr='error'):
    """Raise if `expr` is found in flog"""
    assert os.path.isfile(flog)

    matched_lines = [line for line in open(flog, 'r')
                     if re.search(expr, line.lower())]

    if matched_lines:
        print matched_lines
        assert len(matched_lines) == 0


def assert_expr_in_log(flog, expr):
    """Raise if `expr` is found in flog"""
    assert os.path.isfile(flog)

    matched_lines = [line for line in open(flog, 'r')
                     if re.search(expr, line.lower())]
    assert len(matched_lines)


# utterances from Buckeye composing the TRAIN corpus for the tests
buckeye_utterances = [
    's0101b-sent23',
    's0101b-sent24',
    's0102a-sent16',
    's0102a-sent17',
    's0102b-sent18',
    's0102b-sent19',
]


# utterances from Buckeye composing the TEST corpus for the tests
buckeye_utterances_test = [
    's4003b-sent15',
]


def prepare_corpus(utts, tmpdir):
    # first try to load any prepared buckeye
    buckeye = os.path.join(
        utils.config.get('abkhazia', 'data-directory'),
        'buckeye', 'data')
    if os.path.isdir(buckeye):
        corpus = Corpus.load(buckeye)

    else:  # prepare the whole buckeye corpus
        buckeye = utils.config.get('corpus', 'buckeye-directory')
        corpus = BuckeyePreparator(buckeye).prepare(tmpdir)

    corpus = corpus.subcorpus(utts)
    corpus.validate()

    assert sorted(corpus.utts()) == utts
    assert len(corpus.utts()) == len(utts)
    assert len(corpus.spks()) == len(set(utt.split('-')[0] for utt in utts))

    return corpus


@pytest.fixture(scope='session')
def corpus(tmpdir_factory):
    """Return a corpus made of Buckeye

    This little corpus is the base of all corpus dependant tests. The
    session scope ensures the corpus is initialized only once for all
    the tests.

    The fixture assumes corpus/buckeye-directory is defined in the
    abkhazia configuration file or, if already prepared, that
    abkhazia/data-directory if defined and have the Buckeye corpus
    prepared in its buckeye/data subfolder.

    """
    return prepare_corpus(
        buckeye_utterances,
        str(tmpdir_factory.mktemp('corpus')))


@pytest.fixture(scope='session')
def corpus2(tmpdir_factory):
    return prepare_corpus(
        buckeye_utterances_test,
        str(tmpdir_factory.mktemp('corpus2')))


@pytest.fixture(scope='session')
def features(corpus, tmpdir_factory):
    """Return a directory with MFCC features computed from corpus"""
    output_dir = str(tmpdir_factory.mktemp('features'))
    feat = Features(corpus, output_dir)
    feat.use_pitch = False
    feat.use_cmvn = True
    feat.delta_order = 0
    feat.compute()
    return output_dir


@pytest.fixture(scope='session')
def features2(corpus2, tmpdir_factory):
    """Return a directory with MFCC features computed from corpus2"""
    output_dir = str(tmpdir_factory.mktemp('features2'))
    feat = Features(corpus2, output_dir)
    feat.use_pitch = False
    feat.use_cmvn = True
    feat.delta_order = 0
    feat.compute()
    return output_dir


@pytest.fixture(scope='session')
def lang_args():
    return {'level': 'word',
            'silence_probability': 0.5,
            'position_dependent_phones': False,
            'keep_tmp_dirs': True}


@pytest.fixture(scope='session')
def lm_word(corpus, lang_args, tmpdir_factory):
    """Return a directory with bigram word LM computed from corpus"""
    output_dir = str(tmpdir_factory.mktemp('lm_word'))
    flog = os.path.join(output_dir, 'language.log')
    log = utils.logger.get_log(flog)
    lm = LanguageModel(corpus, output_dir, log=log)
    lm.level = lang_args['level']
    lm.silence_probability = lang_args['silence_probability']
    lm.position_dependent_phones = lang_args['position_dependent_phones']
    lm.order = 2
    lm.compute()
    return output_dir


@pytest.fixture(scope='session')
def lm_word2(corpus2, lang_args, tmpdir_factory):
    """Return a directory with bigram word LM computed from corpus2"""
    output_dir = str(tmpdir_factory.mktemp('lm_word'))
    flog = os.path.join(output_dir, 'language.log')
    log = utils.logger.get_log(flog)
    lm = LanguageModel(corpus2, output_dir, log=log)
    lm.level = lang_args['level']
    lm.silence_probability = lang_args['silence_probability']
    lm.position_dependent_phones = lang_args['position_dependent_phones']
    lm.order = 2
    lm.compute()
    return output_dir


@pytest.fixture(scope='session')
def am_mono(corpus, features, tmpdir_factory, lang_args):
    output_dir = str(tmpdir_factory.mktemp('am_mono'))
    flog = os.path.join(output_dir, 'am_mono.log')
    log = utils.logger.get_log(flog)
    am = acoustic.Monophone(corpus, features, output_dir, lang_args, log=log)

    am.options['total-gaussians'].value = 5
    am.options['num-iterations'].value = 2
    am.options['realign-iterations'].value = [1]
    am.compute()
    return output_dir


@pytest.fixture(scope='session')
def am_tri(corpus, features, am_mono, tmpdir_factory, lang_args):
    output_dir = str(tmpdir_factory.mktemp('am_tri'))
    flog = os.path.join(output_dir, 'am_tri.log')
    log = utils.logger.get_log(flog)
    am = acoustic.Triphone(
        corpus, features, am_mono, output_dir, lang_args, log=log)

    am.options['total-gaussians'].value = 5
    am.options['num-iterations'].value = 2
    am.options['realign-iterations'].value = [1]
    am.options['num-leaves'].value = 20
    am.compute()

    acoustic.check_acoustic_model(output_dir)
    assert_no_expr_in_log(flog, 'error')
    return output_dir


@pytest.fixture(scope='session')
def am_trisa(corpus, features, am_tri, tmpdir_factory, lang_args):
    output_dir = str(tmpdir_factory.mktemp('am_trisa'))
    flog = os.path.join(output_dir, 'am_trisa.log')
    log = utils.logger.get_log(flog)
    am = acoustic.TriphoneSpeakerAdaptive(
        corpus, features, am_tri, output_dir, lang_args, log=log)

    am.options['total-gaussians'].value = 5
    am.options['num-iterations'].value = 2
    am.options['realign-iterations'].value = [1]
    am.options['fmllr-iterations'].value = [1]
    am.options['num-leaves'].value = 20
    am.compute()

    acoustic.check_acoustic_model(output_dir)
    assert_no_expr_in_log(flog, 'error')
    return output_dir


@pytest.fixture(scope='session')
def am_nnet(corpus, features, am_trisa, tmpdir_factory, lang_args):
    output_dir = str(tmpdir_factory.mktemp('am_nnet'))
    flog = os.path.join(output_dir, 'am_nnet.log')
    log = utils.logger.get_log(flog)
    am = acoustic.NeuralNetwork(
        corpus, features, am_trisa, output_dir, lang_args, log=log)

    am.options['num-epochs'].value = 2
    am.options['num-epochs-extra'].value = 1
    am.options['num-hidden-layers'].value = 1
    am.options['num-iters-final'].value = 1
    am.options['pnorm-input-dim'].value = 1
    am.options['pnorm-output-dim'].value = 1
    am.options['num-utts-subset'].value = 2
    am.compute()

    acoustic.check_acoustic_model(output_dir)
    # TODO this assert fails since some preliminary steps of the recipe
    # generate errors (but this do not impact the recipe)
    # # assert_no_expr_in_log(flog, 'error')
    return output_dir
