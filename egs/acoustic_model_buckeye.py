#!/usr/bin/env python
#
# Copyright 2016 Mathieu Bernard
#
# You can redistribute this program and/or modify it under the terms
# of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
"""Exemple of acoustic models training and evaluation using abkhazia
on the Buckeye corpus (English read speech).

5% for train, 95% for test.

"""
import os
import sys
import tempfile

import abkhazia.utils as utils
import abkhazia.corpus.prepare.buckeye_preparator as buckeye
import abkhazia.models.features
import abkhazia.models.language_model
import abkhazia.models.acoustic

# The path to the raw Buckeye distribution
BUCKEYE_RAW = utils.config.get('corpus', 'buckeye-directory')


def init_deps(output_dir, log):
    """setup corpus, features and language model needed for am training"""
    tmpdir = tempfile.mkdtemp(dir='/dev/shm')

    try:
        # import Buckeye in abkhazia format
        corpus = buckeye.BuckeyePreparator(BUCKEYE_RAW, log=log).prepare(
            os.path.join(tmpdir, 'wavs'),
            keep_short_utts=False)
        train_corpus, test_corpus = corpus.split(
            train_prop=0.05, by_speakers=False)
        train_corpus.save(os.path.join(output_dir, 'train', 'data'))
        test_corpus.save(os.path.join(output_dir, 'test', 'data'))

        # compute features for train corpus (with default params from
        # config file)
        train_feats_dir = os.path.join(output_dir, 'train', 'features')
        feats = abkhazia.models.features.Features(
            train_corpus, train_feats_dir, log=log)
        feats.compute()

        # compute lm for train corpus (again with default params)
        train_lm_dir = os.path.join(output_dir, 'train', 'lm')
        lm = abkhazia.models.language_model.LanguageModel(
            train_corpus, train_lm_dir, log=log)
        lm.order = 2
        lm.level = 'word'
        lm.compute()

    finally:
        # cleanup temp directory
        utils.remove(tmpdir)


def main(compute_init=False):
    log = utils.logger.get_log(verbose=True, header_in_stdout=False)
    output_dir = os.path.join(
        os.path.dirname(__file__), 'acoustic_model_buckeye')

    if compute_init:
        init_deps(output_dir, log)

    train_corpus = abkhazia.corpus.Corpus.load(
        os.path.join(output_dir, 'train', 'data'))
    train_feats_dir = os.path.join(output_dir, 'train', 'features')
    train_lm_dir = os.path.join(output_dir, 'train', 'lm')

    # compute monophone model
    am_mono_dir = os.path.join(output_dir, 'train', 'am_mono')
    am_mono = abkhazia.models.acoustic.Monophone(
        train_corpus, train_lm_dir, train_feats_dir,
        am_mono_dir, log=log)
    am_mono.delete_recipe = False
    am_mono.set_option('num-iterations', 4)
    am_mono.set_option('total-gaussians', 10)
    am_mono.set_option('realign-iterations', [1])
    am_mono.compute()

    # compute triphone model
    am_tri_dir = os.path.join(output_dir, 'train', 'am_tri')
    am_tri = abkhazia.models.acoustic.Triphone(
        train_corpus, train_lm_dir, train_feats_dir,
        am_mono_dir, am_tri_dir, log=log)
    am_tri.delete_recipe = False
    am_tri.set_option('num-iterations', 4)
    am_tri.set_option('total-gaussians', 10)
    am_tri.set_option('realign-iterations', [3])
    am_tri.set_option('beam', 2)
    am_tri.set_option('num-leaves', 5)
    am_tri.compute()

    # compute triphone spkeaker adpted model
    am_trisa_dir = os.path.join(output_dir, 'train', 'am_tri_sa')
    am_trisa = abkhazia.models.acoustic.TriphoneSpeakerAdapted(
        train_corpus, train_lm_dir, train_feats_dir,
        am_tri_dir, am_trisa_dir, log=log)
    am_trisa.delete_recipe = False
    am_trisa.set_option('num-iterations', 4)
    am_trisa.set_option('total-gaussians', 10)
    am_trisa.set_option('realign-iterations', [3])
    am_trisa.set_option('beam', 2)
    am_trisa.set_option('num-leaves', 5)
    am_trisa.compute()

    # evaluate it (WER on test corpus)


if __name__ == '__main__':
    sys.exit(main())
