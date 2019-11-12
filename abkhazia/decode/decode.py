# Copyright 2016 Thomas Schatz, Xuan-Nga Cao, Mathieu Bernard
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
"""Decode unknown speech on a trained acoustic model"""

import os
import shutil

import abkhazia.abstract_recipe as abstract_recipe
import abkhazia.language as language
import abkhazia.features as features
import abkhazia.acoustic as acoustic
import abkhazia.utils as utils

from abkhazia.decode import _mkgraph
from abkhazia.decode import _decoder
from abkhazia.decode import _decoder_fmllr
from abkhazia.decode import _decoder_nnet
from abkhazia.decode import _score


decoders = {
    'si': _decoder,
    'sa': _decoder_fmllr,
    'nnet': _decoder_nnet}


class Decode(abstract_recipe.AbstractRecipe):
    name = 'decode'

    def __init__(self, corpus, lm_dir, feats_dir, am_dir, output_dir,
                 decode_type=None, log=utils.logger.null_logger(),
                 fmllr_dir=None):
        super(Decode, self).__init__(corpus, output_dir, log=log)
        self.feat_dir = os.path.abspath(feats_dir)
        self.lm_dir = os.path.abspath(lm_dir)
        self.am_dir = os.path.abspath(am_dir)
        # if fmllr are already computed and given in input:
        self.fmllr_dir = (
            os.path.abspath(fmllr_dir) if fmllr_dir is not None
            else None)

        self.am_type = acoustic.model_type(am_dir)
        self._decoder_type = {
            'mono': 'si',
            'tri': 'si',
            'tri-sa': 'sa',
            'nnet': 'nnet'}[self.am_type]
        if decode_type and self._decoder_type != decode_type:
            raise IOError(
                'Cannot setup decoder, acoustic model '
                'and decoder type are not compatible')
        self._decoder = decoders[self._decoder_type]

        self.mkgraph_opts = _mkgraph.options()
        self.decode_opts = self._decoder.options()
        self.score_opts = _score.options()

    def check_parameters(self):
        """Raise if the decoding parameters are not correct"""
        super(Decode, self).check_parameters()

        features.Features.check_features(self.feat_dir)
        language.check_language_model(self.lm_dir)
        acoustic.check_acoustic_model(self.am_dir)

        self.meta.source += '\n' + '\n'.join((
            'features = {}'.format(self.feat_dir),
            'language model = {}'.format(self.lm_dir),
            'acoustic model = {}'.format(self.am_dir)))

    def set_option(self, name, value):
        """Set option `name` to `value`

        Raise KeyError on unknown option and TypeError if the value
        cannot be converted to the option type

        """
        if name in self.mkgraph_opts:
            self.mkgraph_opts[name].value = self.mkgraph_opts[name].type(value)
        elif name in self.decode_opts:
            self.decode_opts[name].value = self.decode_opts[name].type(value)
        elif name in self.score_opts:
            self.score_opts[name].value = self.score_opts[name].type(value)
        else:
            raise KeyError('Option {} not valid'.format(name))

    def create(self):
        super(Decode, self).create()

        # setup local/score.sh
        self.a2k.setup_score()

        # copy features scp files in the recipe_dir
        features.Features.export_features(
            self.feat_dir,
            os.path.join(self.recipe_dir, 'data', self.name))

    def run(self):
        """Run the created recipe and decode speech data"""
        # build the full decoding graph
        graph_dir = _mkgraph.mkgraph(self)

        # decode the corpus according to input am type
        self._decoder.decode(self, graph_dir)

    def export(self):
        """Copy the whole <recipe-dir>/decode to <output-dir>, copy
        <recipe-dir>/graph to <output-dir>/graph

        """
        self.log.debug('exporting results to %s', self.output_dir)

        result_directory = os.path.join(self.recipe_dir, 'decode')
        for path in utils.list_directory(result_directory, abspath=True):
            if os.path.isdir(path):
                shutil.copytree(path, os.path.join(
                    self.output_dir, os.path.basename(path)))
            else:
                shutil.copy(path, self.output_dir)

        shutil.copytree(
            os.path.join(self.recipe_dir, 'graph'),
            os.path.join(self.output_dir, 'graph'))

        super(Decode, self).export()
