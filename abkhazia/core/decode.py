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
# along with abkhazia. If not, see <http://www.gnu.org/licenses/>.
"""Provides the Decode class"""

import gzip
import multiprocessing
import os

import abkhazia.core.language_model as language_model
from abkhazia.core.features import export_features
from abkhazia.core.kaldi_path import kaldi_path
import abkhazia.core.abstract_recipe as abstract_recipe
import abkhazia.utils as utils


class Decode(abstract_recipe.AbstractRecipe):
    """Decode an abkhazia corpus from acoustic and language models

    Instantiates and run a kaldi recipe to compute either phone
    posteriograms or a transcription estimation from an abkhazia
    corpus, a language model an dan acoustic model.

    The language model an acoustic model should be computed from a
    train set, while the decoding should be estimated from a test set
    (use the SplitCorpus class)

    """
    name = 'decode'

    def __init__(self, corpus_dir, recipe_dir=None, verbose=False):
        super(Decode, self).__init__(corpus_dir, recipe_dir, verbose)

        # setup default values for parameters from the configuration
        def config(name):
            return utils.config.get(self.name, name)
        # self.use_pitch = config('use-pitch')
        self.acoustic_scale = config('acoustic-scale')

        self.feat_dir = None
        self.am_dir = None
        self.lm_dir = None
        self.is_monophone_lm = None

        ncores = multiprocessing.cpu_count()
        self.njobs = ncores

    def _check_njobs(self, njobs):
        # if we run jobs locally, make sure we have enough cores
        ncores = multiprocessing.cpu_count()
        cmd = utils.config.get('kaldi', 'train-cmd')
        if 'queue' not in cmd and ncores < njobs:
                self.log.warning(
                    'asking {0} cores but {1} available, reducing {0} -> {1}'
                    .format(njobs, ncores))
                njobs = ncores
        return njobs

    @staticmethod
    def _check_template(param, name, target):
        if param is None:
            raise RuntimeError('non specified {} model'.format(name))
        if not os.path.isfile(target):
            raise RuntimeError('non valid {} model: {} not found'
                               .format(name, target))

    def _check_acoustic_model(self):
        self._check_template(
            self.am_dir, 'acoustic', os.path.join(self.am_dir, 'final.mdl'))

    def _check_language_model(self):
        # check the requested files are here
        for target in ['oov.int', 'G.fst', 'G.arpa.gz']:
            self._check_template(
                self.lm_dir, 'language', os.path.join(self.lm_dir, target))

        # retrieve LM parameters
        lm_level, lm_order = language_model.read_params(self.lm_dir)
        self.log.debug(
            'language model is a {} level {}-gram'.format(lm_level, lm_order))
        self.is_monophone_lm = True if lm_order == 1 else False

    def _mkgraph(self):
        """Instantiate a full decoding graph (HCLG)"""
        target = os.path.join(self.recipe_dir, 'graph')
        self.log.info(
            'computing full decoding graph in %s', target)
        if not os.path.isdir(target):
            os.makedirs(target)

        command = (
            '{0} {1} utils/mkgraph.sh {2} {3} {4} {5}'.format(
                os.path.join(
                    'utils', utils.config.get('kaldi', 'highmem-cmd')),
                os.path.join(target, 'mkgraph.log'),
                '--mono' if self.is_monophone_lm else '',
                self.lm_dir,
                self.am_dir,
                target))

        self.log.debug('running %s', command)
        utils.jobs.run(command, stdout=self.log.debug,
                       env=kaldi_path(), cwd=self.recipe_dir)
        return target

    def _decode(self, origin):
        target = os.path.join(self.recipe_dir, 'decode')
        self.log.info(
            'decoding and computing WER in %s', target)
        if not os.path.isdir(target):
            os.makedirs(target)

        command = (
            'steps/decode.sh --nj {0} --cmd "{1}" --model {2} {3} {4} {5}'.format(
                self.njobs,
                utils.config.get('kaldi', 'decode-cmd'),
                os.path.join(self.am_dir, 'final.mdl'),
                origin,
                os.path.join('data', self.name),
                target))

        self.log.debug('running %s', command)
        utils.jobs.run(command, stdout=self.log.debug,
                       env=kaldi_path(), cwd=self.recipe_dir)
        return target

    def check_parameters(self):
        """Raise if the decoding parameters are not correct"""
        self._check_language_model()
        self._check_acoustic_model()

        self.njobs = self._check_njobs(self.njobs)

    def create(self):
        # local folder
        self.a2k.setup_lexicon()
        self.a2k.setup_phones()
        self.a2k.setup_silences()
        self.a2k.setup_variants()

        # setup data files
        desired_utts = self.a2k.desired_utterances(njobs=self.njobs)
        self.a2k.setup_text(desired_utts=desired_utts)
        self.a2k.setup_utt2spk(desired_utts=desired_utts)
        self.a2k.setup_segments(desired_utts=desired_utts)
        self.a2k.setup_wav(desired_utts=desired_utts)

        # setup other files and folders
        self.a2k.setup_score()
        self.a2k.setup_wav_folder()
        self.a2k.setup_kaldi_folders()
        self.a2k.setup_machine_specific_scripts()

        export_features(
            self.feat_dir,
            os.path.join(self.recipe_dir, 'data', self.name),
            self.corpus_dir)

    def run(self):
        """Run the created recipe and decode speech data"""
        self.check_parameters()

        # decoding
        res_dir = self._mkgraph()
        res_dir = self._decode(res_dir)

    def export(self):
        pass
