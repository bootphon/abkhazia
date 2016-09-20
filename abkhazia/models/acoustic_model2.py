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
"""Provides classes for computing acoustic models with Kaldi"""

import os
import shutil

from abkhazia.models.features import Features
from abkhazia.models.language_model import check_language_model
from abkhazia.models.abstract_recipe import AbstractRecipe
import abkhazia.utils as utils


class AcousticModelBase(AbstractRecipe):
    """Base class of acoustic models trainers

    Instantiates and run a kaldi recipe to train a HMM-GMM model on
    an abkhazia corpus and a language model

    Parameters:
    -----------

    corpus (Corpus): abkhazia corpus to process

    features_dir (str): path to the features directory

    languagemodel_dir (str): path to the language model directory

    output_dir (str): path to the created recipe and results

    log (logging.Logger): where to send log messages

    """
    name = 'acoustic'

    def __init__(self, corpus, features_dir, languagemodel_dir,
                 output_dir, log=utils.logger.null_logger):
        super(AcousticModelBase, self).__init__(corpus, output_dir, log=log)

        self.features_dir = os.path.abspath(features_dir)
        self.languagemodel_dir = os.path.abspath(languagemodel_dir)
        self.data_dir = os.path.join(self.recipe_dir, 'data', 'acoustic')

    def check_parameters(self):
        """Check language model and features are valid, setup metadata"""
        super(AcousticModelBase, self).check_parameters()
        check_language_model(self.languagemodel_dir)
        self.meta.source += '\n'.join((
            'features directory:\t{}'.format(self.features_dir),
            'language model directory:\t{}'.format(self.languagemodel_dir)))

    def create(self):
        super(AcousticModelBase, self).create()

        # copy features scp files in the recipe_dir
        Features.export_features(
            self.features_dir, self.data_dir)

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

        super(AcousticModelBase, self).export()

    def run(self):
        self._align()
        self._train()

    def _run_am_command(self, command, target, message):
        self.log.info(message)
        if not os.path.isdir(target):
            os.makedirs(target)

        self._run_command(command, verbose=False)
        return target

    def _align(self):
        raise NotImplementedError

    def _train(self):
        raise NotImplementedError


class Monophone(AcousticModelBase):
    def _align(self):
        pass

    def _train(self):
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
                self.languagemodel_dir,
                target))
        return self._run_am_command(command, target, message)


class Triphone(AcousticModelBase):
    def _align(self):



# class SpeakerAdaptiveTriphone(AcousticModelBase):
#     pass


# class DNN(AcousticModelBase):
#     pass
