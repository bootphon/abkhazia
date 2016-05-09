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
import shutil

import abkhazia.core.abstract_recipe as abstract_recipe
import abkhazia.utils as utils


def export_features(feat_dir, target_dir, corpus_dir, copy=False):
    """Export feats.scp, cmvn.scp and wav.scp from feat_dir to target_dir

    If copy is True, make copies instead of links. Raises IOError if
    one of the file isn't in feat_dir.

    """
    # sanity checks
    for d in (feat_dir, target_dir, corpus_dir):
        if not os.path.isdir(d):
            raise IOError('{} is not a directory'.format(d))

    # export feats and cmvn
    for scp in ('feats.scp', 'cmvn.scp'):
        origin = os.path.join(feat_dir, scp)
        if not os.path.isfile(origin):
            raise IOError('{} not found'.format(origin))

        target = os.path.join(target_dir, scp)
        if copy:
            shutil.copy(origin, target)
        else:
            os.symlink(origin, target)

    # export wav, correct paths to be relative to corpus_dir/data/wavs
    # instead of recipe_dir
    origin = os.path.join(feat_dir, 'wav.scp')
    if not os.path.isfile(origin):
            raise IOError('{} not found'.format(origin))

    prefix = os.path.join(corpus_dir, 'data', 'wavs')
    with open(os.path.join(target_dir, 'wav.scp'), 'w') as target:
        for line in open(origin, 'r').readlines():
            line = line.strip().split(' ')
            target.write('{} {}\n'.format(
                line[0], os.path.join(prefix, line[1].split('/')[-1])))


class Features(abstract_recipe.AbstractTmpRecipe):
    """Compute MFCC features from an abkhazia corpus"""
    name = 'features'

    def __init__(self, corpus_dir, output_dir=None, verbose=False):
        super(Features, self).__init__(corpus_dir, output_dir, verbose)

        self.njobs = multiprocessing.cpu_count()
        self.use_pitch = (
            True if utils.config.get('features', 'use-pitch') == 'true'
            else False)

    def _setup_conf_dir(self):
        """Setup the conf files for feature extraction"""
        conf_dir = os.path.join(self.recipe_dir, 'conf')
        if os.path.exists(conf_dir):
            shutil.rmtree(conf_dir)
        os.mkdir(conf_dir)

        # create mfcc.conf file (following what seems to be commonly
        # used in other kaldi recipes)
        with open(os.path.join(conf_dir, 'mfcc.conf'), mode='w') as out:
            out.write("--use-energy=false   # only non-default option.\n")

        # create empty pitch.conf file (required when using mfcc +
        # pitch features)
        with open(os.path.join(conf_dir, 'pitch.conf'), mode='w') as out:
            pass

    def _compute_features(self):
        script = ('steps/make_mfcc_pitch.sh' if self.use_pitch
                  else 'steps/make_mfcc.sh')
        self.log.info('computing MFCC features%s',
                      ' with pitch' if self.use_pitch else '')

        self._run_command(
            script + ' --nj {0} --cmd "{1}" {2} {3} {4}'.format(
                self.njobs,
                utils.config.get('kaldi', 'train-cmd'),
                os.path.join('data', self.name),
                os.path.join('exp', 'make_mfcc', self.name),
                self.output_dir))

    def _compute_cmvn_stats(self):
        self.log.info('computing CMVN statistics')
        self._run_command(
            'steps/compute_cmvn_stats.sh {0} {1} {2}'.format(
                os.path.join('data', self.name),
                os.path.join('exp', 'make_mfcc', self.name),
                self.output_dir))

    def create(self):
        super(Features, self).create()
        self._setup_conf_dir()

    def run(self):
        self._compute_features()
        self._compute_cmvn_stats()

    def export(self):
        for scp in utils.list_files_with_extension(self.output_dir, '.scp'):
            utils.remove(scp)

        export_features(
            os.path.join(self.recipe_dir, 'data', self.name),
            self.output_dir,
            self.corpus_dir,
            copy=True)

        super(Features, self).export()
