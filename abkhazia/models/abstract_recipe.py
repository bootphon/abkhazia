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
"""Provides the AbstractRecipe class"""

import multiprocessing
import os

import abkhazia.utils as utils
from abkhazia.kaldi import kaldi_path, Abkhazia2Kaldi


class AbstractRecipe(utils.AbkhaziaBase):
    """A base class for kaldi recipes operating on an abkhazia corpus

    If you want the recipe directory in output_dir/recipe, set
    self.delete_recipe to False (default is True)

    """
    name = NotImplemented
    """The recipe's name"""

    def __init__(self, corpus, output_dir, log=utils.null_logger()):
        super(AbstractRecipe, self).__init__(log=log)
        self.njobs = utils.default_njobs()
        self.corpus = corpus
        self.meta.source = 'corpus = {}'.format(self.corpus.meta.source)
        self.meta.name = self.name + ' on corpus ' + self.corpus.meta.name

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        self.output_dir = os.path.abspath(output_dir)

        # init the recipe dir  as a subdirectory of output_dir
        self.recipe_dir = os.path.join(self.output_dir, 'recipe')
        if not os.path.isdir(self.recipe_dir):
            os.makedirs(self.recipe_dir)

        # if True, delete the recipe_dir on instance destruction
        self.delete_recipe = True

        # init the abkhazia2kaldi converter
        self.a2k = Abkhazia2Kaldi(
            self.corpus, self.recipe_dir, name=self.name, log=self.log)

    def __del__(self):
        try:
            if self.delete_recipe:
                utils.remove(self.recipe_dir, safe=True)
        except AttributeError:  # if raised from __init__
            pass

    def _run_command(self, command, verbose=True):
        """Run the command as a subprocess, wrapper on utils.jobs"""
        if verbose is True:
            self.log.debug('running %s', command)

        utils.jobs.run(
            command,
            stdout=self.log.debug,
            env=kaldi_path(),
            cwd=self.recipe_dir)

    def _check_njobs(self, local=False):
        """If we run jobs locally, make sure we have enough cores"""
        ncores = multiprocessing.cpu_count()
        queued = not local or 'queue' in utils.config.get('kaldi', 'train-cmd')
        if queued and ncores < self.njobs:
            self.log.warning(
                'asking {0} cores but {1} available, reducing {0} -> {1}'
                .format(self.njobs, ncores))
            self.njobs = ncores

    def check_parameters(self):
        """Perform sanity checks on recipe parameters, raise on error"""
        self._check_njobs()

    def create(self):
        """Create the recipe in `self.recipe_dir`

        Setup Kaldi scripts and environment in self.recipe_dir

        """
        self.check_parameters()

        # local folder
        self.a2k.setup_lexicon()
        self.a2k.setup_phones()
        self.a2k.setup_silences()
        self.a2k.setup_variants()

        # setup data files
        self.a2k.setup_text()
        self.a2k.setup_utt2spk()
        self.a2k.setup_segments()
        self.a2k.setup_wav()

        # setup other files and folders
        self.a2k.setup_wav_folder()
        self.a2k.setup_kaldi_folders()
        self.a2k.setup_machine_specific_scripts()

    def run(self):
        """Run the recipe by calling Kaldi scripts

        This method is abstract and must be implemented in child
        classes.

        """
        raise NotImplementedError

    def export(self):
        """Copy result files to self.output_dir

        This method must be specialized in child classes.

        """
        self.meta.save(os.path.join(self.output_dir, 'meta.txt'))
