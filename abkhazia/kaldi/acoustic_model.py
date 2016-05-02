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
"""Provides the AcousticModel class"""

import os
import multiprocessing

from abkhazia.kaldi.kaldi_path import kaldi_path
import abkhazia.kaldi.abstract_recipe as abstract_recipe
import abkhazia.utils as utils


class AcousticModel(abstract_recipe.AbstractRecipe):
    """Compute an acoustic model from an abkhazia corpus

    Instantiates and run a kaldi recipe to train a HMM-GMM model on
    an abkhazia corpus and a language model

    Parameters:
        corpus_dir (str): path to an abkhazia corpus
        recipe_dir (str): path to the created recipe and results
        verbose (bool): if True send more messages to the logger
        model_type (str): The type of model to train in 'mono', 'tri', 'tri-sa'

    Attributes:
        lang (str): path to the language model directory
        njobs_train (int): Number of parallel jobs for computing model
        njobs_local (int): Number of parallel jobs for pre/post computing
        num_states_si (int)
        num_gauss_si (int)
        num_states_sa (int)
        num_gauss_sa (int)

    """
    name = 'acoustic'

    def __init__(self, corpus_dir, recipe_dir=None,
                 verbose=False, model_type='mono'):
        super(AcousticModel, self).__init__(corpus_dir, recipe_dir, verbose)
        self.model_type = model_type

        # setup default values for parameters from the configuration
        def config(name):
            return utils.config.get(self.name, name)
        self.num_states_si = config('num-states-si')
        self.num_gauss_si = config('num-gauss-si')
        self.num_states_sa = config('num-states-sa')
        self.num_gauss_sa = config('num-gauss-sa')

        self.lang = None
        self.feat = None

        ncores = multiprocessing.cpu_count()
        self.njobs_train = ncores
        self.njobs_local = ncores

    def _check_features(self):
        if self.feat is None:
            raise RuntimeError('non specified features')

        if not os.path.isdir(self.feat):
            raise RuntimeError(
                'features not found: {}'.format(self.feat))

        for target in ('feats.scp', 'cmvn.scp'):
            o = os.path.join(self.feat, 'data', 'features', target)
            if not os.path.isfile(o):
                raise RuntimeError('{} not found'.format(o))

            t = os.path.join(self.recipe_dir, 'data', self.name, target)
            self.log.info('Using %s', o)
            os.symlink(o, t)

    def _check_language_model(self):
        if self.lang is None:
            raise RuntimeError('non specified language model')

        # ensure it's a directory and we have both oov.int and
        # G.fst in it
        if not os.path.isdir(self.lang):
            raise RuntimeError(
                'language model not found: {}.\n'.format(self.lang))
        for target in ['oov.int', 'G.fst']:
            if not os.path.isfile(os.path.join(self.lang, target)):
                raise RuntimeError(
                    'non valid language model: {} not found in {}'
                    .format(target, self.lang))

    def _check_njobs(self, njobs, local=False):
        # if we run jobs locally, make sure we have enough cores
        # TODO refactor
        ncores = multiprocessing.cpu_count()
        if local and ncores < njobs:
            self.log.warning(
                'asking {0} cores but {1} available, reducing {0} -> {1}'
                .format(njobs, ncores))
            njobs = ncores

        if not local and 'queue' not in utils.config.get('kaldi', 'train-cmd'):
            if ncores < njobs:
                self.log.warning(
                    'asking {0} cores but {1} available, reducing {0} -> {1}'
                    .format(njobs, ncores))
                njobs = ncores
        return njobs

    def _check_model_type(self):
        if self.model_type not in ['mono', 'tri', 'tri-sa']:
            raise RuntimeError(
                "model type '{}' not in 'mono', 'tri', 'tri-sa'"
                .format(self.model_type))

    def _monophone_train(self):
        # Flat start and monophone training, with delta-delta features.
        # This script applies cepstral mean normalization (per speaker).
        target = os.path.join(self.recipe_dir, 'exp', 'mono')
        self.log.info('training the monophone model in %s', target)

        if not os.path.isdir(target):
            os.makedirs(target)

        command = ('steps/train_mono.sh --nj {0} --cmd "{1}" {2} {3} {4}'
                   .format(
                       self.njobs_train,
                       utils.config.get('kaldi', 'train-cmd'),
                       os.path.join('data', self.name),
                       self.lang,
                       target))

        self.log.debug('running %s', command)
        utils.jobs.run(command, stdout=self.log.debug,
                       env=kaldi_path(), cwd=self.recipe_dir)
        return target

    def _triphone_align(self, origin):
        # Computes training alignments using a model with delta or
        # LDA+MLLT features.
        target = os.path.join(self.recipe_dir, 'exp', 'mono_ali')
        self.log.info(
            'force-aligning corpus with the monophone model in %s', target)

        if not os.path.isdir(target):
            os.makedirs(target)

        command = ('steps/align_si.sh --nj {0} --cmd "{1}" {2} {3} {4} {5}'
                   .format(
                       self.njobs_train,
                       utils.config.get('kaldi', 'train-cmd'),
                       os.path.join('data', self.name),
                       self.lang,
                       origin,
                       target))

        self.log.debug('running %s', command)
        utils.jobs.run(command, stdout=self.log.debug,
                       env=kaldi_path(), cwd=self.recipe_dir)

        return target

    def _triphone_train(self, origin):
        target = os.path.join(self.recipe_dir, 'exp', 'tri')
        self.log.info(
            'training speaker-independant triphone model in %s', target)

        if not os.path.isdir(target):
            os.makedirs(target)

        command = ('steps/train_deltas.sh --cmd "{0}" {1} {2} {3} {4} {5} {6}'
                   .format(
                       utils.config.get('kaldi', 'train-cmd'),
                       self.num_states_si,
                       self.num_gauss_si,
                       os.path.join('data', self.name),
                       self.lang,
                       origin,
                       target))

        self.log.debug('running %s', command)
        utils.jobs.run(command, stdout=self.log.debug,
                       env=kaldi_path(), cwd=self.recipe_dir)

        return target

    def _sa_triphone_align(self, origin):
        target = os.path.join(self.recipe_dir, 'exp', 'tri_ali_fmllr')
        self.log.info(
            'forced-aligning corpus with the triphone model in %s', target)

        if not os.path.isdir(target):
            os.makedirs(target)

        command = ('steps/align_fmllr.sh --nj {0} --cmd "{1}" {2} {3} {4} {5}'
                   .format(
                       self.njobs_train,
                       utils.config.get('kaldi', 'train-cmd'),
                       os.path.join('data', self.name),
                       self.lang,
                       origin,
                       target))

        self.log.debug('running %s', command)
        utils.jobs.run(command, stdout=self.log.debug,
                       env=kaldi_path(), cwd=self.recipe_dir)

        return target

    def _sa_triphone_train(self, origin):
        target = os.path.join(self.recipe_dir, 'exp', 'tri_sa')
        self.log.info(
            'training speaker-adaptive triphone model in %s', target)

        if not os.path.isdir(target):
            os.makedirs(target)

        command = ('steps/train_sat.sh --cmd "{0}" {1} {2} {3} {4} {5} {6}'
                   .format(
                       utils.config.get('kaldi', 'train-cmd'),
                       self.num_states_sa,
                       self.num_gauss_sa,
                       os.path.join('data', self.name),
                       self.lang,
                       origin,
                       target))

        self.log.debug('running %s', command)
        utils.jobs.run(command, stdout=self.log.debug,
                       env=kaldi_path(), cwd=self.recipe_dir)

        return target

    def _export(self, result_directory):
        # finally symlink the result to a constant directory
        final_directory = os.path.join(
            self.recipe_dir, 'exp', 'acoustic_model')
        utils.remove(final_directory, safe=True)
        os.symlink(result_directory, final_directory)

    def check_parameters(self):
        """Raise if the acoustic modeling parameters are not correct"""
        self._check_features()
        self._check_language_model()
        self._check_model_type()

        self.njobs_train = self._check_njobs(self.njobs_train)
        self.njobs_local = self._check_njobs(self.njobs_local, local=True)

    def create(self):
        """Initialize the recipe data in `self.recipe_dir`"""
        # local folder
        self.a2k.setup_lexicon()
        self.a2k.setup_phones()
        self.a2k.setup_silences()
        self.a2k.setup_variants()

        # setup data files
        desired_utts = self.a2k.desired_utterances(njobs=self.njobs_local)
        self.a2k.setup_text(desired_utts=desired_utts)
        self.a2k.setup_utt2spk(desired_utts=desired_utts)
        self.a2k.setup_segments(desired_utts=desired_utts)
        self.a2k.setup_wav(desired_utts=desired_utts)

        # setup other files and folders
        self.a2k.setup_wav_folder()
        self.a2k.setup_conf_dir()
        self.a2k.setup_kaldi_folders()
        self.a2k.setup_machine_specific_scripts()

    def run(self):
        """Run the created recipe and compute the acoustic model"""
        self.check_parameters()

        # monophone
        result_directory = self._monophone_train()
        if self.model_type == 'mono':
            return self._export(result_directory)

        # triphone
        result_directory = self._triphone_align(result_directory)
        result_directory = self._triphone_train(result_directory)
        if self.model_type == 'tri':
            return self._export(result_directory)

        # speaker adaptive triphone
        result_directory = self._sa_triphone_align(result_directory)
        result_directory = self._sa_triphone_train(result_directory)
        return self._export(result_directory)
