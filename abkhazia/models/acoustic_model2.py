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
    def __init__(self, corpus, features_dir, languagemodel_dir,
                 output_dir=None, log=utils.logger.null_logger):
        super(AcousticModelBase, self).__init__(corpus, output_dir, log=log)

        self.features_dir = features_dir
        self.languagemodel_dir = languagemodel_dir
        self.data_dir = os.path.join(self.recipe_dir, 'data', 'acoustic')

    def create(self):
        super(AcousticModelBase, self).create()

        # copy features scp files in the recipe_dir
        Features.export_features(
            self.features_dir, self.data_dir)

    def _run_am_command(self, command, target, message):
        self.log.info(message)
        if not os.path.isdir(target):
            os.makedirs(target)

        self._run_command(command, verbose=False)
        return target


class Monophone(AcousticModelBase):
    def __init__(self, corpus, features_dir, languagemodel_dir,
                 output_dir=None, log=utils.logger.null_logger):
        super(Monophone, self).__init__(
            corpus, features_dir, languagemodel_dir,
            output_dir=None, log=utils.logger.null_logger)

    def run(self):
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


# class Triphone(AcousticModelBase):
#     pass


# class SpeakerAdaptiveTriphone(AcousticModelBase):
#     pass


# class DNN(AcousticModelBase):
#     pass
