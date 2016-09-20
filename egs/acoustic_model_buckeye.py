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

import os
import sys
import tempfile

import abkhazia.utils as utils
import abkhazia.corpus.prepare.buckeye_preparator as buckeye
import abkhazia.models.features
import abkhazia.models.language_model
import abkhazia.models.acoustic_model2

# The path to the raw Buckeye distribution
BUCKEYE_RAW = '/home/mbernard/data/databases/BUCKEYE_revised_bootphon'


def init_deps(output_dir, log):
    """setup corpus, features and language model needed for am training"""
    tmpdir = tempfile.mkdtemp(dir='/dev/shm')

    try:
        # import Buckeye in abkhazia format
        corpus = buckeye.BuckeyePreparator(BUCKEYE_RAW, log=log).prepare(
            os.path.join(tmpdir, 'wavs'),
            keep_short_utts=False)
        train_corpus, test_corpus = corpus.split(train_prop=0.5)
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
    am_mono = abkhazia.models.acoustic_model2.Monophone(
        train_corpus, train_feats_dir, train_lm_dir,
        output_dir=am_mono_dir, log=log)
    am_mono.compute()

    # evaluate it (WER on test corpus)


if __name__ == '__main__':
    sys.exit(main())
