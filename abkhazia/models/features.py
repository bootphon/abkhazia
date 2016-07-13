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

import os
import shutil
import joblib

import abkhazia.models.abstract_recipe as abstract_recipe
import abkhazia.utils as utils


def _delta_joblib_fnc(i, instance):
    """A tweak to compute deltas inplace and in parallel using joblib

    class methods are not pickable so we pass a Features instance as a
    parameter instead of using self.

    i is a 1-length tuple containing the scp to compute delta on

    """
    i = i[0]
    o = i + '_tmp'
    try:
        instance._run_command(
            'add-deltas --delta-order={0} scp:{1} ark:{2}'.format(
                instance.delta_order, i, o), verbose=False)

        instance._run_command(
            'copy-feats ark:{} ark,scp:{},{}'.format(
                o, i.replace('.scp', '.ark'), i),
            verbose=False)
    finally:
        utils.remove(o, safe=True)


def export_features(feat_dir, target_dir, corpus, copy=False):
    """Export wav.scp from feat_dir to target_dir

    Both `feat_dir` and `target_dir` are assumed to exist.

    If copy is True, make copies instead of links. Raises IOError if
    one of the input files isn't in feat_dir.

    """
    # sanity checks
    for _dir in (feat_dir, target_dir):
        if not os.path.isdir(_dir):
            raise IOError('{} is not a directory'.format(_dir))

    # export wav.scp, correct paths to be relative to corpus
    # instead of recipe_dir
    origin = os.path.join(feat_dir, 'wav.scp')
    if not os.path.isfile(origin):
        raise IOError('{} not found'.format(origin))
    with open(os.path.join(target_dir, 'wav.scp'), 'w') as scp:
        for line in open(origin, 'r'):
            key = line.strip().split(' ')[0]
            wav = corpus.wavs[key]
            scp.write('{} {}\n'.format(key, wav))


class Features(abstract_recipe.AbstractRecipe):
    """Compute speech features from an abkhazia corpus"""
    name = 'features'

    def __init__(self, corpus, output_dir, log=utils.null_logger()):
        super(Features, self).__init__(corpus, output_dir, log=log)

        self.type = utils.config.get('features', 'type')
        if self.type not in ['mfcc', 'plp', 'fbank']:
            raise IOError('unknown feature type "{}"'.format(self.type))

        self.use_pitch = utils.str2bool(
            utils.config.get('features', 'use-pitch'))

        self.use_cmvn = utils.str2bool(
            utils.config.get('features', 'use-cmvn'))

        self.delta_order = utils.config.getint('features', 'delta-order')

        # options sent to the Kaldi feature extractor (in a config file)
        self.features_options = [('use-energy', 'false')]

    def _setup_conf_dir(self):
        """Setup the conf files for feature extraction"""
        conf_dir = os.path.join(self.recipe_dir, 'conf')
        if os.path.exists(conf_dir):
            shutil.rmtree(conf_dir)
        os.mkdir(conf_dir)

        # create mfcc.conf file (following what seems to be commonly
        # used in other kaldi recipes)
        with open(
                os.path.join(conf_dir, '{}.conf'.format(self.type)),
                mode='w') as out:
            for o in self.features_options:
                out.write("--{}={}\n".format(o[0], o[1]))

        # create empty pitch.conf file (required when using pitch
        # related Kaldi scripts)
        if self.use_pitch:
            with open(os.path.join(conf_dir, 'pitch.conf'), mode='w') as out:
                pass

    def _get_kaldi_script(self):
        script = 'steps/make_' + self.type
        if self.use_pitch:
            script += '_pitch'
        script += '.sh'
        return script

    def _compute_features(self):
        """Wrapper on steps/make_**type**_pitch.sh or steps/make_**type**.sh"""
        script = self._get_kaldi_script()
        self.log.info('computing %s features%s',
                      self.type,
                      ' with pitch' if self.use_pitch else '')

        self._run_command(
            script + ' --nj {0} --cmd "{1}" {2} {3} {4}'.format(
                self.njobs,
                utils.config.get('kaldi', 'train-cmd'),
                os.path.join('data', self.name),
                os.path.join('exp', 'make_{}'.format(self.type), self.name),
                self.output_dir),
            verbose=False)

    def _compute_delta(self):
        """Wrapper on add-deltas Kaldi executable

        The order of the computed deltas is given by the attribute
        self.delta_order. Raise IOError if self.delta_order == 0

        """
        if self.delta_order <= 0:
            raise IOError(
                'Cannot compute deltas because order is lower than 1')
        self.log.info('computing deltas (order %s)', self.delta_order)

        # get the input scp files with raw features
        inputs = [f for f in utils.list_files_with_extension(
            self.output_dir, '.scp', abspath=True, recursive=False)
                  if 'cmvn' not in f]

        # compute deltas in parallel, one job per scp file
        joblib.Parallel(
            n_jobs=self.njobs, verbose=1, backend='threading')(
                joblib.delayed(_delta_joblib_fnc)(i, self)
                for i in zip(inputs))

        # merge the output scp files into a single one, and delete them
        output_scp = os.path.join(self.output_dir, 'feats.scp')
        with open(output_scp, 'w') as outfile:
            for infile in inputs:
                outfile.write(open(infile, 'r').read())
                utils.remove(infile)

    def _compute_cmvn_stats(self):
        """Wrapper on steps/compute_cmvn_stats.sh"""
        self.log.info('computing CMVN statistics')
        self._run_command(
            'steps/compute_cmvn_stats.sh {0} {1} {2}'.format(
                os.path.join('data', self.name),
                os.path.join('exp', 'make_{}'.format(self.type), self.name),
                self.output_dir),
            verbose=False)

    def create(self):
        super(Features, self).create()
        self._setup_conf_dir()

    def run(self):
        self._compute_features()

        if self.use_cmvn:
            self._compute_cmvn_stats()

        if self.delta_order != 0:
            self._compute_delta()

    def export(self):
        super(Features, self).export()

        if self.use_cmvn:
            shutil.move(
                os.path.join(self.output_dir, 'cmvn_features.scp'),
                os.path.join(self.output_dir, 'cmvn.scp'))

        export_features(
            os.path.join(self.recipe_dir, 'data', self.name),
            self.output_dir,
            self.corpus,
            copy=True)

        # # delete temp scp files in output dir
        # tmp_scp = (
        #     [f.replace('.ark', '.scp')
        #      for f in utils.list_directory(self.output_dir, abspath=True)
        #      if f[-4:] == '.ark'] +
        #     [os.path.join(self.output_dir, 'cmvn_features.scp')]
        #     if self.use_cmvn else [])

        # for scp in tmp_scp:
        #     utils.remove(scp, safe=True)
