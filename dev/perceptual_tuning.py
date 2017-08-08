#!/usr/bin/env python
#
# Copyright 2017 Thomas Schatz, Xuan-Nga Cao, Mathieu Bernard
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
"""Script for the perceptual tuning project

Take 2 corpora as input, corpus A and corpus B. Corpus A must be in
valid abkhazia format. Corpus B has minimal componants to be
determined TODO.

Step 0
  - import corpus A and B in abkhazia format
  - optional subsampling (about 1h each for dev)

Step 1 (corpus A)
  - MFCC features
  - position dependant phones
  - word bigram language model
  - speaker adaptive triphone acoustic model

Step 2 (corpus A)
  - decode it on itself
  - compute WER

Step 3 (corpus B)
  - MFCC features
  - position dependant phones
  - decode on AM from step 1
  - output the phone posteriograms

"""

import os

from abkhazia.corpus.prepare.buckeye_preparator import BuckeyePreparator
from abkhazia.corpus.prepare.xitsonga_preparator import XitsongaPreparator
from abkhazia.corpus import Corpus
from abkhazia.features import Features
from abkhazia.language import LanguageModel
from abkhazia.decode import Decode
from abkhazia.acoustic import (
    Monophone, Triphone, TriphoneSpeakerAdaptive, NeuralNetwork)
from abkhazia.utils.logger import get_log


# data directory where to write all the data
DATA_DIR = '/home/mathieu/data/perceptual_tuning'

# raw distribution and preparator of the corpus A
NAME_A = 'buckeye'
PATH_A = '/home/mathieu/data/databases/BUCKEYE_revised_bootphon'
PREP_A = BuckeyePreparator

# raw distribution and preparator of the corpus B
NAME_B = 'xitsonga'
PATH_B = '/home/mathieu/data/databases/nchlt_Xitsonga'
PREP_B = XitsongaPreparator

# setup a global logger for the whole script
log = get_log(os.path.join(DATA_DIR, 'log'),
              verbose=True, header_in_stdout=True)


def prepare(preparator, path, wavs_dir, corpus_dir, subsampling=False):
    corpus = preparator(path, log=log).prepare(wavs_dir)
    if subsampling:
        corpus = subsample(corpus)
    corpus.save(corpus_dir, copy_wavs=False, force=True)


def subsample(corpus, nspeakers=4, duration=3600):
    """Return a subcorpus made of nspeakers of approx. duration"""
    log.info('subsampling corpus %s', corpus.meta.name)

    spk2utt = corpus.spk2utt()
    utt2duration = corpus.utt2duration()
    spk2duration = {k: sum(utt2duration[v] for v in vv)
                    for k, vv in spk2utt.items()}

    # speakers sorted by the difference (spk_duration - target_duration)
    speakers = sorted(spk2duration.items(), key=lambda x: abs(
        int(x[1]) - (duration / nspeakers)))[:nspeakers]

    utts = []
    for s in speakers:
        utts += spk2utt[s[0]]

    log.info('subsampled total duration: %ss from %s speakers',
             sum(utt2duration[u] for u in utts), nspeakers)

    return corpus.subcorpus(utts)


def step_0(subsampling=False):
    """Import corpora A and B in abkhazia format

    Produces the A/data and B/data folders

    If `subsampling` is True, prepare only a subpart of the corpora
    (for dev purposes, target corpus is 1h, 4 speakers)

    """
    log.info('STEP 0: preparing corpora %s and %s', NAME_A, NAME_B)

    corpus_a = prepare(
        PREP_A,
        PATH_A,
        os.path.join(DATA_DIR, NAME_A, 'wavs'),
        os.path.join(DATA_DIR, NAME_A, 'data'),
        subsampling=subsampling)

    corpus_b = prepare(
        PREP_B,
        PATH_B,
        os.path.join(DATA_DIR, NAME_B, 'wavs'),
        os.path.join(DATA_DIR, NAME_B, 'data'),
        subsampling=subsampling)

    return (corpus_a, corpus_b)


def step_1(am_type='nnet'):
    """Compute wpd AM/LM on corpus A"""
    log.info('STEP 1: training AM on %s', NAME_A)

    # load the input corpus
    corpus_dir = os.path.join(DATA_DIR, NAME_A)
    corpus = Corpus.load(os.path.join(corpus_dir, 'data'))

    # init output directories
    feat_dir = os.path.join(corpus_dir, 'features')
    lm_dir = os.path.join(corpus_dir, 'word_bigram')
    am_mono_dir = os.path.join(corpus_dir, 'am_mono')
    am_tri_dir =  os.path.join(corpus_dir, 'am_tri')
    am_trisa_dir =  os.path.join(corpus_dir, 'am_trisa')
    am_nnet_dir =  os.path.join(corpus_dir, 'am_nnet')

    # prepare_lang arguments for the acoustic models
    lang_args = {
        'silence_probability': 0.5,
        'position_dependent_phones': True,
        'keep_tmp_dirs': True}

    # compute mfcc features
    Features(
        corpus,
        feat_dir,
        type='mfcc',
        delta_order=0,
        use_pitch=False,
        use_cmvn=True,
        delete_recipe=False,
        log=log).compute()

    # compute word bigram with wpd phones
    LanguageModel(
        corpus,
        lm_dir,
        level='word',
        order=2,
        silence_probability=0.5,
        position_dependent_phones=True,
        delete_recipe=False,
        log=log).compute()

    # train monophone acoustic model
    Monophone(
        corpus,
        feat_dir,
        am_mono_dir,
        lang_args,
        delete_recipe=False,
        log=log).compute()
    if am_type == 'mono':
        return

    # train triphone actoustic model
    Triphone(
        corpus,
        feat_dir,
        am_mono_dir,
        am_tri_dir,
        lang_args,
        delete_recipe=False,
        log=log).compute()
    if am_type == 'tri':
        return

    # train triphone speaker adpative acoustic model
    TriphoneSpeakerAdaptive(
        corpus,
        feat_dir,
        am_tri_dir,
        am_trisa_dir,
        lang_args,
        delete_recipe=False,
        log=log).compute()
    if am_type == 'trisa':
        return

    # train deep network acoustic model
    NeuralNetwork(
        corpus,
        feat_dir,
        am_trisa_dir,
        am_nnet_dir,
        lang_args,
        delete_recipe=False,
        log=log).compute()


def step_2(am_type='nnet'):
    """Decode and score corpus A on A"""
    log.info('STEP 2: decoding %s on itself and computing WER...',
             os.path.basename(corpus_dir))

    # load the input corpus
    corpus_dir = os.path.join(DATA_DIR, NAME_A)
    corpus = Corpus.load(os.path.join(corpus_dir, 'data'))

    # init output directories
    feat_dir = os.path.join(corpus_dir, 'features')
    lm_dir = os.path.join(corpus_dir, 'word_bigram')
    am_dir = os.path.join(corpus_dir, 'am_' + am_type)
    decode_dir = os.path.join(corpus_dir, 'decode')

    Decode(
        corpus,
        lm_dir,
        feat_dir,
        am_dir,
        decode_dir,
        delete_recipe=False,
        log=log).compute()


def step_3(am_type='nnet'):
    """Decode corpus B on A"""
    log.info('STEP 3: decode wavs from %s on corpus %s ...',
             NAME_B, NAME_A)

    # load the input corpus
    corpus_b_dir = os.path.join(DATA_DIR, NAME_B)
    corpus = Corpus.load(os.path.join(corpus_b_dir, 'data'))

    # init input directories
    corpus_a_dir = os.path.join(DATA_DIR, NAME_A)
    lm_dir = os.path.join(corpus_a_dir, 'word_bigram')
    am_dir = os.path.join(corpus_a_dir, 'am_' + am_type)

    # init output directories
    feat_dir = os.path.join(corpus_b_dir, 'features')
    decode_dir = os.path.join(corpus_b_dir, 'decode')

    # compute features for corpus B
    Features(
        corpus,
        feat_dir,
        type='mfcc',
        delta_order=0,
        use_pitch=False,
        use_cmvn=True,
        delete_recipe=False,
        log=log).compute()

    # decode corpus B on AM/LM from corpus A
    Decode(
        corpus,
        lm_dir,
        feat_dir,
        am_dir,
        decode_dir,
        delete_recipe=False,
        log=log).compute()


def main(subsampling=True, am_type='mono'):
    log.info('output directory is %s', DATA_DIR)

    # prepare the 2 corpora
    step_0(subsampling=subsampling)

    # compute wpd LM/AM on corpus A
    step_1(am_type=am_type)

    # decode and score corpus A on A
    step_2(am_type=am_type)

    # decode corpus B on A
    step_3(am_type=am_type)


if __name__ == '__main__':
    main()
