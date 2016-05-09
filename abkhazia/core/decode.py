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

import os

import abkhazia.core.language_model as language_model
import abkhazia.core.acoustic_model as acoustic_model
import abkhazia.core.abstract_recipe as abstract_recipe
import abkhazia.utils as utils
from abkhazia.core.features import export_features


class Decode(abstract_recipe.AbstractTmpRecipe):
    """Decode an abkhazia corpus from acoustic and language models

    Instantiates and run a kaldi recipe to compute either phone
    posteriograms or a transcription estimation from an abkhazia
    corpus, a language model an dan acoustic model.

    The language model an acoustic model should be computed from a
    train set, while the decoding should be estimated from a test set
    (use the SplitCorpus class)

    """
    name = 'decode'

    def __init__(self, corpus_dir, output_dir=None, verbose=False):
        super(Decode, self).__init__(corpus_dir, output_dir, verbose)

        self.acoustic_scale = utils.config.get(self.name, 'acoustic-scale')
        self.feat_dir = None
        self.am_dir = None
        self.lm_dir = None

    def _mkgraph(self):
        """Instantiate a full decoding graph (HCLG)"""
        self.log.info('computing full decoding graph')

        target = os.path.join(self.recipe_dir, 'graph')
        if not os.path.isdir(target):
            os.makedirs(target)

        _, lm_order = language_model.read_params(self.lm_dir)
        self._run_command(
            '{0} {1} utils/mkgraph.sh {2} {3} {4} {5}'.format(
                os.path.join(
                    'utils', utils.config.get('kaldi', 'highmem-cmd')),
                os.path.join(target, 'mkgraph.log'),
                '--mono' if lm_order == 1 else '',
                self.lm_dir,
                self.am_dir,
                target))

        return target

    def _decode(self, origin):
        self.log.info('decoding and computing WER')

        target = os.path.join(self.recipe_dir, 'decode')
        if not os.path.isdir(target):
            os.makedirs(target)

        self._run_command(
            'steps/decode.sh --nj {0} --cmd "{1}" --model {2} {3} {4} {5}'
            .format(
                self.njobs,
                utils.config.get('kaldi', 'decode-cmd'),
                os.path.join(self.am_dir, 'final.mdl'),
                origin,
                os.path.join('data', self.name),
                target))

        return target

    def check_parameters(self):
        """Raise if the decoding parameters are not correct"""
        super(Decode, self).check_parameters()
        language_model.check_language_model(self.lm_dir)
        acoustic_model.check_acoustic_model(self.am_dir)

    def create(self):
        super(Decode, self).create()

        export_features(
            self.feat_dir,
            os.path.join(self.recipe_dir, 'data', self.name),
            self.corpus_dir)

    def run(self):
        """Run the created recipe and decode speech data"""
        res_dir = self._mkgraph()
        res_dir = self._decode(res_dir)
        return res_dir

    def export(self):
        super(Decode, self).export()
