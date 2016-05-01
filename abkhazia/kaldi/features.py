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
"""Provides the Features class"""

import multiprocessing
import os

from abkhazia.kaldi.kaldi_path import kaldi_path
import abkhazia.kaldi.abstract_recipe as abstract_recipe
import abkhazia.utils as utils


class Features(abstract_recipe.AbstractRecipe):
    """Compute MFCC features from an abkhazia corpus"""
    name = 'features'

    def __init__(self, corpus_dir, recipe_dir=None, verbose=False):
        super(Features, self).__init__(corpus_dir, recipe_dir, verbose)

        self.njobs = multiprocessing.cpu_count()
        self.use_pitch = (
            True if utils.config.get('features', 'use-pitch') == 'true'
            else False)

    def _compute_features(self):
        script = ('steps/make_mfcc_pitch.sh' if self.use_pitch
                  else 'steps/make_mfcc.sh')
        self.log.info('computing features with %s', script)

        command = (
            script + ' --nj {0} --cmd "{1}" {2} {3} {4}'.format(
                self.njobs,
                utils.config.get('kaldi', 'train-cmd'),
                os.path.join('data', self.name),
                os.path.join('exp', 'make_mfcc', self.name),
                'mfcc'))

        # self.log.debug('running %s', command)
        utils.jobs.run(command, stdout=self.log.debug,
                       env=kaldi_path(), cwd=self.recipe_dir)

    def _compute_cmvn_stats(self):
        command = 'steps/compute_cmvn_stats.sh {0} {1} {2}'.format(
            os.path.join('data', self.name),
            os.path.join('exp', 'make_mfcc', self.name),
            'mfcc')

        # self.log.debug('running %s', command)
        utils.jobs.run(command, stdout=self.log.debug,
                       env=kaldi_path(), cwd=self.recipe_dir)

    def create(self):
        desired_utts = self.a2k.desired_utterances(njobs=self.njobs)
        self.a2k.setup_text(desired_utts=desired_utts)
        self.a2k.setup_utt2spk(desired_utts=desired_utts)
        self.a2k.setup_segments(desired_utts=desired_utts)
        self.a2k.setup_wav(desired_utts=desired_utts)

        self.a2k.setup_wav_folder()
        self.a2k.setup_conf_dir()
        self.a2k.setup_kaldi_folders()
        self.a2k.setup_machine_specific_scripts()

    def run(self):
        self._compute_features()
        self._compute_cmvn_stats()

    def export(self):
        pass
