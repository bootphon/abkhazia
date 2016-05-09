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
import shutil
import tempfile

import abkhazia.utils as utils
import abkhazia.core.abkhazia2kaldi as abkhazia2kaldi
from abkhazia.core.kaldi_path import kaldi_path


class AbstractRecipe(object):
    """A base class for creating kaldi recipes from an abkhazia corpus"""
    name = NotImplemented
    """The recipe's name"""

    def __init__(self, corpus_dir, recipe_dir=None,
                 verbose=False, log_file=None):
        self.verbose = verbose

        # check corpus_dir
        if not os.path.isdir(corpus_dir):
            raise IOError("directory doesn't exist: {}".format(corpus_dir))
        self.corpus_dir = corpus_dir

        # init the recipe dir
        self.recipe_dir = self.corpus_dir if recipe_dir is None else recipe_dir
        if not os.path.isdir(self.recipe_dir):
            os.makedirs(self.recipe_dir)

        # init the log
        if log_file is None:
            log_file = os.path.join(self.output_dir, self.name + '.log')
        self.log = utils.log2file.get_log(log_file, verbose)
        self.log.debug('reading corpus from %s', self.corpus_dir)

        # init njobs
        self.njobs = utils.default_njobs()

        # init the abkhazia2kaldi converter
        self.a2k = abkhazia2kaldi.Abkhazia2Kaldi(
            corpus_dir, self.recipe_dir,
            name=self.name, verbose=verbose, log=self.log)

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
        # if we run jobs locally, make sure we have enough cores
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
        desired_utts = self.a2k.desired_utterances(njobs=self.njobs)
        self.a2k.setup_text(desired_utts=desired_utts)
        self.a2k.setup_utt2spk(desired_utts=desired_utts)
        self.a2k.setup_segments(desired_utts=desired_utts)
        self.a2k.setup_wav(desired_utts=desired_utts)

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

        This method is abstract and must be implemented in child
        classes.

        """
        raise NotImplementedError


class AbstractTmpRecipe(AbstractRecipe):
    """Write the recipe in a temprary directory

    Provide an output_dir attribute where to put results files. The
    recipe directory is deleted on instance destruction. Depending if
    we run jobs locally or queued, the temp dir is created in /tmp or
    in output_dir respectively.

    If you want the recipe directory in output_dir/recipe, set
    self.delete_recipe to False (default is True)

    """
    def __init__(self, corpus_dir, output_dir, verbose=False):
        # if True, delete the recipe_dir on instance destruction
        self.delete_recipe = True

        # setup an empty output dir
        if os.path.isdir(output_dir):
            raise OSError(
                'output directory already existing: {}'
                .format(output_dir))
        else:
            os.makedirs(output_dir)
        self.output_dir = os.path.abspath(output_dir)

        # setup recipe_dir as a temp dir
        cmd = utils.config.get('kaldi', 'train-cmd')
        recipe_dir = tempfile.mkdtemp(
            dir=self.output_dir if 'queue' in cmd else None)

        super(AbstractTmpRecipe, self).__init__(
            corpus_dir, recipe_dir, verbose=verbose)

    def export(self):
        if not self.delete_recipe:
            target = os.path.join(self.output_dir, 'recipe')
            self.log.info('copying recipe to %s', target)
            shutil.move(self.recipe_dir, target)

    def __del__(self):
        try:
            self.log.debug(
                'removing recipe directory {}'.format(self.recipe_dir))
            utils.remove(self.recipe_dir, safe=True)
        except AttributeError:  # if raised from __init__
            pass
