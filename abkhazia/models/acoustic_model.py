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
import shutil

from abkhazia.models.features import Features
from abkhazia.models.language_model import check_language_model
from abkhazia.models.abstract_recipe import AbstractRecipe
import abkhazia.utils as utils


def check_acoustic_model(am_dir):
    """Raise IOError if final.mdl is not in am_dir"""
    utils.check_directory(am_dir, ['final.mdl'], name='acoustic model')


class AcousticModel(AbstractRecipe):
    """Compute an acoustic model from an abkhazia corpus

    Instantiates and run a kaldi recipe to train a HMM-GMM model on
    an abkhazia corpus and a language model

    Parameters:
    -----------

    corpus (Corpus): abkhazia corpus to process

    output_dir (str): path to the created recipe and results

    log (logging.Logger): where to send log messages

    Attributes:
    -----------

    lang (str): path to the language model directory

    feat (str): path to the features directory

    model_type (str): The type of model to train in 'mono', 'tri',
        'tri-sa'

    njobs (int): Number of parallel jobs to use

    num_states_si, num_gauss_si, num_states_sa, num_gauss_sa (int) :
        Number of states/Gaussians in speaker adaptive/independant
        models

    """
    name = 'acoustic'

    def __init__(self, corpus, output_dir=None, log=utils.logger.null_logger):
        super(AcousticModel, self).__init__(corpus, output_dir, log=log)

        # setup default values for parameters from the configuration
        def config(name):
            return utils.config.get(self.name, name)
        self.model_type = config('model')
        self.num_states_si = config('num-states-si')
        self.num_gauss_si = config('num-gauss-si')
        self.num_states_sa = config('num-states-sa')
        self.num_gauss_sa = config('num-gauss-sa')

        self.lang = None
        self.feat = None
        self.data_dir = os.path.join(self.recipe_dir, 'data', self.name)

    def _check_model_type(self):
        if self.model_type not in ['mono', 'tri', 'tri-sa']:
            raise RuntimeError(
                "model type '{}' not in 'mono', 'tri', 'tri-sa'"
                .format(self.model_type))

    def _run_am_command(self, command, target, message):
        self.log.info(message)
        if not os.path.isdir(target):
            os.makedirs(target)

        self._run_command(command, verbose=False)
        return target

    def _monophone_train(self):
        # Flat start and monophone training, with delta-delta features.
        # This script applies cepstral mean normalization (per speaker).
        message = 'training monophone model'
        target = os.path.join(self.recipe_dir, 'exp', 'mono')
        command = (
            'steps/train_mono.sh --nj {0} --cmd "{1}" {2} {3} {4}'
            .format(
                self.njobs,
                utils.config.get('kaldi', 'train-cmd'),
                self.data_dir,
                self.lang,
                target))
        return self._run_am_command(command, target, message)

    def _triphone_align(self, origin):
        # Computes training alignments using a model with delta or
        # LDA+MLLT features.
        message = 'force-aligning monophone model'
        target = os.path.join(self.recipe_dir, 'exp', 'mono_ali')
        command = (
            'steps/align_si.sh --nj {0} --cmd "{1}" {2} {3} {4} {5}'
            .format(
                self.njobs,
                utils.config.get('kaldi', 'train-cmd'),
                self.data_dir,
                self.lang,
                origin,
                target))
        return self._run_am_command(command, target, message)

    def _triphone_train(self, origin):
        message = 'training speaker-independant triphone model'
        target = os.path.join(self.recipe_dir, 'exp', 'tri')
        command = (
            'steps/train_deltas.sh --cmd "{0}" {1} {2} {3} {4} {5} {6}'
            .format(
                utils.config.get('kaldi', 'train-cmd'),
                self.num_states_si,
                self.num_gauss_si,
                self.data_dir,
                self.lang,
                origin,
                target))
        return self._run_am_command(command, target, message)

    def _sa_triphone_align(self, origin):
        message = 'forced-aligning triphone model'
        target = os.path.join(self.recipe_dir, 'exp', 'tri_ali_fmllr')
        command = (
            'steps/align_fmllr.sh --nj {0} --cmd "{1}" {2} {3} {4} {5}'
            .format(
                self.njobs,
                utils.config.get('kaldi', 'train-cmd'),
                self.data_dir,
                self.lang,
                origin,
                target))
        return self._run_am_command(command, target, message)

    def _sa_triphone_train(self, origin):
        message = 'training speaker-adaptive triphone model'
        target = os.path.join(self.recipe_dir, 'exp', 'tri_sa')
        command = (
            'steps/train_sat.sh --cmd "{0}" {1} {2} {3} {4} {5} {6}'
            .format(
                utils.config.get('kaldi', 'train-cmd'),
                self.num_states_sa,
                self.num_gauss_sa,
                self.data_dir,
                self.lang,
                origin,
                target))
        return self._run_am_command(command, target, message)

    def check_parameters(self):
        super(AcousticModel, self).check_parameters()
        check_language_model(self.lang)
        self._check_model_type()
        self.meta.source += ', feat = {}, lm = {}'.format(self.feat, self.lang)

    def create(self):
        super(AcousticModel, self).create()

        # copy features scp files in the recipe_dir
        Features.export_features(
            self.feat,
            os.path.join(self.recipe_dir, 'data', self.name))

    def run(self):
        """Run the created recipe and compute the acoustic model"""
        # monophone
        out = self._monophone_train()

        # triphone
        if 'tri' in self.model_type:
            out = self._triphone_align(out)
            out = self._triphone_train(out)

            # speaker adaptive triphone
            if self.model_type == 'tri-sa':
                out = self._sa_triphone_align(out)
                out = self._sa_triphone_train(out)

        return out

    def export(self, result_directory):
        """Copy model files to output_dir"""
        for path in (
                # exclude files starting with numbers, as we want only
                # final state
                p for p in utils.list_directory(result_directory, abspath=True)
                if not os.path.basename(p)[0].isdigit()):
            if os.path.isdir(path):  # for log subdir
                shutil.copytree(
                    path,
                    os.path.join(self.output_dir, os.path.basename(path)))
            else:
                shutil.copy(path, self.output_dir)

        super(AcousticModel, self).export()

    def compute(self):
        self.create()
        self.export(self.run())
