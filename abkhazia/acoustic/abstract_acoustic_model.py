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
""""Abstract base class of acoustic models trainers"""

import os
import shutil

from abkhazia.features import Features
from abkhazia.abstract_recipe import AbstractRecipe
from abkhazia.utils import prepare_lang
import abkhazia.utils as utils
import abkhazia.kaldi as kaldi

make_option = kaldi.options.make_option


def model_type(am_dir):
    """Return the type of the trained model

    Read in meta.txt, or raise IOError if not found

    TODO could be parsed from final.mdl ?

    """
    meta = os.path.join(am_dir, 'meta.txt')
    if not os.path.isfile(meta):
        raise IOError('file not found: {}'.format(meta))

    for line in utils.open_utf8(meta, 'r'):
        if line.startswith('acoustic model type'):
            return line.split(':')[1].strip()

    raise IOError('acoustic model type not found in {}'.format(meta))


def check_acoustic_model(am_dir):
    """Raise IOError if final.mdl is not in am_dir"""
    utils.check_directory(
        am_dir,
        ['final.mdl'],
        name='acoustic model')

    utils.check_directory(
        os.path.join(am_dir, 'lang'),
        ['L.fst', 'phones.txt', 'words.txt'],
        name='lang')

    utils.check_directory(
        os.path.join(am_dir, 'lang', 'phones'),
        ['silence.csl', 'disambig.int'],
        name='lang/phones')


class AbstractAcousticModel(AbstractRecipe):
    """Abstract base class of acoustic models trainers

    Instantiates and run a Kaldi recipe to train a HMM-GMM model on an
    abkhazia corpus, along with attached features.

    Parameters:
    -----------

    corpus (Corpus): abkhazia corpus to process

    src_dir (str): path to the source directory (the model `n-1`), or
    a features_dir (if n=1, i.e. on monophone models)

    output_dir (str): path to the created recipe and results

    log (logging.Logger): where to send log messages

    """
    # Linked to 'abkhazia acoustic' from command line
    name = 'acoustic'

    model_type = NotImplemented

    options = NotImplemented

    def __init__(self, corpus, input_dir, output_dir, lang_args,
                 log=utils.logger.null_logger):
        super(AbstractAcousticModel, self).__init__(
            corpus, output_dir, log=log)

        self.input_dir = os.path.abspath(input_dir)
        self.data_dir = os.path.join(self.recipe_dir, 'data', 'acoustic')
        self.lang_dir = os.path.join(self.output_dir, 'lang')
        self.lang_args = lang_args

    def check_parameters(self):
        """Check features are valid, setup metadata"""
        super(AbstractAcousticModel, self).check_parameters()

        # check lang_args are OK
        lang = self.lang_args
        assert lang['level'] in ('word', 'phone')
        assert (lang['silence_probability'] <= 1
                and lang['silence_probability'] > 0)
        assert isinstance(lang['position_dependent_phones'], bool)
        assert isinstance(lang['keep_tmp_dirs'], bool)

        # write the meta.txt file
        self.meta.source += '\n'.join((
            'input directory:\t{}'.format(self.input_dir),
            'acoustic model type:\t{}'.format(self.model_type)))

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

        # create lang directory with L.fst
        lang = self.lang_args
        prepare_lang.prepare_lang(
            self.corpus,
            self.lang_dir,
            level=lang['level'],
            silence_probability=lang['silence_probability'],
            position_dependent_phones=lang['position_dependent_phones'],
            keep_tmp_dirs=lang['keep_tmp_dirs'],
            log=self.log)

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
        """Return the value of an option given its name"""
        return str(self.options[name])
