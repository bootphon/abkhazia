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

Take 2 corpora as input, corpus A and corpus B, both must be in valid
abkhazia format.

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
  - TODO output the phone posteriograms from the decoded lattices

"""

import os
import shutil

from abkhazia.utils.logger import get_log
from abkhazia.corpus import Corpus
from abkhazia.features import Features
from abkhazia.language import LanguageModel
from abkhazia.decode import Decode
from abkhazia.acoustic import (
    Monophone, Triphone, TriphoneSpeakerAdaptive, NeuralNetwork)


###############################
# SETUP PART YOU WANT TO CHANGE
# you may also want to change the call to main at the end of the file

from abkhazia.corpus.prepare.buckeye_preparator import BuckeyePreparator
from abkhazia.corpus.prepare.xitsonga_preparator import XitsongaPreparator

# data directory where to write all the data
DATA_DIR = '/home/mathieu/data/perceptual_tuning'

# name, raw distribution and preparator of the corpus A
NAME_A = 'buckeye'
PREP_A = BuckeyePreparator
PATH_A = '/home/mathieu/data/databases/BUCKEYE_revised_bootphon'

# name, raw distribution and preparator of the corpus B
NAME_B = 'xitsonga'
PREP_B = XitsongaPreparator
PATH_B = '/home/mathieu/data/databases/nchlt_Xitsonga'

# END OF SETUP PART
#####################


# setup a global logger for the whole script, output both to stdout
# and to the DATA_DIR/log file.
log = get_log(
    os.path.join(DATA_DIR, 'log'),
    verbose=True,
    header_in_stdout=True)


def prepare(name, preparator, path, output_dir, subsampling=False):
    """Prepare a corpus, validate it and save it to disk

    :param str name: Name of the prepared corpus

    :param class preparator: Abkhazia preparator class used to prepare
      the corpus.

    :param str path: The path to the corpus raw distribution.

    :param str output_dir: The directory where to save the prepared
      corpus. Create the folders `output_dir`/`name`/{data, wavs}.

    :param bool subsampling: See main() for description.

    """
    # setup the output directories
    corpus_dir = os.path.join(output_dir, name, 'data')
    wavs_dir = os.path.join(output_dir, name, 'wavs')

    # prepare the corpus
    corpus = preparator(path, log=log).prepare(wavs_dir)
    if subsampling:
        corpus = subsample(corpus, name, nspeakers=4, duration=3600)

    # validate and save it
    corpus.validate()
    corpus.save(corpus_dir, copy_wavs=False, force=True)


def subsample(corpus, name, nspeakers=4, duration=3600):
    """Return a subcorpus made of a specified subpart of `corpus`

    TODO That function is clearly not general, it takes whole speakers
    data only and supposes the requested duration to be close to the
    mean duration of speakers in the input corpus.

    :param Corpus corpus: The abkhazia corpus to subsample

    :param int nspeakers: The number of speakers to retain in the
       subsampled corpus.

    :param int duration: The targeted duration in seconds of the
       subsampled corpus.

    """
    log.info('subsampling corpus %s', corpus.meta.name)

    # compute the total speech duration for each speaker
    spk2utt = corpus.spk2utt()
    utt2duration = corpus.utt2duration()
    spk2duration = {spk: sum(utt2duration[utt] for utt in utts)
                    for spk, utts in spk2utt.items()}

    # speakers sorted by the difference (spk_duration -
    # target_duration), take the nspeakers best sorted speakers in the
    # subcorpus.
    speakers = sorted(
        spk2duration.items(),
        key=lambda x: abs(int(x[1]) - (duration / nspeakers))
    )[:nspeakers]

    # the utterances composing the subsampled corpus
    utts = [utt for spk in speakers for utt in spk2utt[spk[0]]]

    log.info('subsampled total duration: %ss from %s speakers',
             sum(utt2duration[u] for u in utts), nspeakers)

    return corpus.subcorpus(utts, name=name, validate=False, prune=True)


def step_1(am_type='nnet'):
    """Compute word position dependant AM/LM on corpus A"""
    log.info('STEP 1: training AM on %s', NAME_A)

    # load the input corpus
    corpus_dir = os.path.join(DATA_DIR, NAME_A)
    corpus = Corpus.load(os.path.join(corpus_dir, 'data'))

    # init output directories
    feat_dir = os.path.join(corpus_dir, 'features')
    lm_dir = os.path.join(corpus_dir, 'word_bigram')
    am_mono_dir = os.path.join(corpus_dir, 'am_mono')
    am_tri_dir = os.path.join(corpus_dir, 'am_tri')
    am_trisa_dir = os.path.join(corpus_dir, 'am_trisa')
    am_nnet_dir = os.path.join(corpus_dir, 'am_nnet')

    # prepare_lang arguments for the language and acoustic models
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
        silence_probability=lang_args['silence_probability'],
        position_dependent_phones=lang_args['position_dependent_phones'],
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
    log.info('STEP 2: decoding %s on itself and computing WER...', NAME_A)

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
    """Decode corpus B on AM/LM from corpus A"""
    log.info(
        'STEP 3: decode wavs from %s on %s model trained on corpus %s',
        NAME_B, am_type, NAME_A)

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
    decoder = Decode(
        corpus,
        lm_dir,
        feat_dir,
        am_dir,
        decode_dir,
        delete_recipe=False,
        log=log)
    decoder.score_opts['skip-scoring'] = True
    decoder.compute()


def main(am_type='trisa', subsampling=True, overwrite=False):
    """Run the whole pipeline from corpora preparation to final decoding

    Setup the data directory DATA_DIR and execute the steps 0 to 4.

    :param str am_type: The acoustic model type to train and to decode
      on. Must be 'mono', 'tri', 'trisa' or 'nnet'. Default is 'trisa'.

    :param bool subsampling: When True, prepare only a subsample of
      the corpora (approximatively 1 hour and 4 speakers). When False
      prepare the whole corpora. Default is False.

    :param bool overwrite: When True erase any content in DATA_DIR at
      startup. When False do not delete anything but mail
      fail. Default is False.

    """
    # setup the data directory
    log.info('output directory is %s', DATA_DIR)
    if overwrite and os.path.isdir(DATA_DIR):
        log.info('erasing content in %s', DATA_DIR)
        shutil.rmtree(DATA_DIR)
    os.makedirs(DATA_DIR)

    # prepare the 2 corpora A and B
    log.info('STEP 0: preparing corpora %s and %s', NAME_A, NAME_B)
    prepare(NAME_A, PREP_A, PATH_A, DATA_DIR, subsampling=subsampling)
    prepare(NAME_B, PREP_B, PATH_B, DATA_DIR, subsampling=subsampling)

    # compute word position dependant LM/AM on corpus A
    step_1(am_type=am_type)

    # decode and score corpus A on the AM
    step_2(am_type=am_type)

    # decode corpus B on the AM
    step_3(am_type=am_type)


if __name__ == '__main__':
    # subtask for dev
    main(am_type='mono', subsampling=True, overwrite=True)

    # # full task
    # main(am_type='nnet', subsampling=False, overwrite=True)
