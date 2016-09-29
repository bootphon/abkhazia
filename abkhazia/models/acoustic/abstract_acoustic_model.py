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

import os
import shutil

from abkhazia.models.features import Features
from abkhazia.models.language_model import check_language_model
from abkhazia.models.abstract_recipe import AbstractRecipe
import abkhazia.utils as utils

make_option = utils.kaldi.options.make_option


class AbstractAcousticModel(AbstractRecipe):
    """Abstract base class of acoustic models trainers

    Instantiates and run a Kaldi recipe to train a HMM-GMM model on an
    abkhazia corpus, along with attached features and language model.

    Parameters:
    -----------

    corpus (Corpus): abkhazia corpus to process

    lm_dir (str): path to the language model directory

    src_dir (str): path to the source directory (the model `n-1`), or
    a features_dir (if n=1, i.e. on monophone models)

    output_dir (str): path to the created recipe and results

    log (logging.Logger): where to send log messages

    """
    # Linked to 'abkhazia acoustic' from command line
    name = 'acoustic'

    model_type = NotImplemented

    options = NotImplemented

    def __init__(self, corpus, lm_dir, input_dir,
                 output_dir, log=utils.logger.null_logger):
        super(AbstractAcousticModel, self).__init__(
            corpus, output_dir, log=log)

        self.input_dir = os.path.abspath(input_dir)
        self.lm_dir = os.path.abspath(lm_dir)
        self.data_dir = os.path.join(self.recipe_dir, 'data', 'acoustic')

    def check_parameters(self):
        """Check language model and features are valid, setup metadata"""
        super(AbstractAcousticModel, self).check_parameters()
        check_language_model(self.lm_dir)

        self.meta.source += '\n'.join((
            'input directory:\t{}'.format(self.input_dir),
            'language model directory:\t{}'.format(self.lm_dir)))

    def set_option(self, name, value):
        """Set option `name` to `value`

        Raise KeyError on unknown option and TypeError if the value
        cannot be converted to the option type

        """
        self.options[name].value = self.options[name].type(value)

    def create(self):
        super(AbstractAcousticModel, self).create()

        # copy features scp files in the recipe_dir
        Features.export_features(self.input_dir, self.data_dir)

    def export(self):
        """Copy model files to output_dir"""
        result_directory = os.path.join(
            self.recipe_dir, 'exp', self.model_type)

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

        super(AbstractAcousticModel, self).export()

    def run(self):
        raise NotImplementedError

    def _run_am_command(self, command, target, message):
        self.log.info(message)
        if not os.path.isdir(target):
            os.makedirs(target)
        self._run_command(command, verbose=False)

    def _opt(self, name):
        """Return the value of an option given its name

        The returned value is converted to string according to its type.
        Lookup in self.options, raise KeyError on unknown option

        TODO This method must be part of utils.options

        """
        t = self.options[name].type
        v = self.options[name].value
        if t is bool:
            return utils.bool2str(v)
        elif t is list:
            return ' '.join(str(i) for i in v)
        return str(v)
