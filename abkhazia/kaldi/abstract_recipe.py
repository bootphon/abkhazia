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

import os
import tempfile

import abkhazia.utils as utils
import abkhazia.kaldi.abkhazia2kaldi as abkhazia2kaldi


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
        self.recipe_dir = os.path.join(self.recipe_dir, self.name)

        if os.path.isdir(self.recipe_dir):
            raise OSError(
                'output directory already existing: {}'
                .format(self.recipe_dir))
        else:
            os.makedirs(self.recipe_dir)

        # init the log
        if log_file is None:
            log_file = os.path.join(
                self.recipe_dir, 'logs', self.name + '.log')
        log_dir = os.path.dirname(log_file)

        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        self.log = utils.log2file.get_log(log_file, verbose)

        # init the abkhazia2kaldi converter
        self.a2k = abkhazia2kaldi.Abkhazia2Kaldi(
            corpus_dir, self.recipe_dir,
            name=self.name, verbose=verbose, log=self.log)

    def create(self, args):
        """Create the recipe in `self.recipe_dir`

        This method is abstract and must be implemented in child
        classes.

        """
        raise NotImplementedError

    def run(self):
        """Run the recipe by calling Kaldi scripts

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

    If you want to preserve the tmp directory, setup self.delete_tmp
    to False (default is True)

    """
    def __init__(self, corpus_dir, output_dir, verbose=False):
        # setup an empty output dir
        self.output_dir = os.path.abspath(output_dir)
        if os.path.isdir(output_dir):
            raise OSError(
                'output directory already existing: {}'
                .format(output_dir))
        else:
            os.makedirs(output_dir)

        # setup recipe_dir as a temp dir
        cmd = utils.config.get('kaldi', 'train-cmd')
        recipe_dir = tempfile.mkdtemp(
            dir=self.output_dir if 'queue' in cmd else None)

        self.delete_tmp = True
        self.to_delete = recipe_dir

        super(AbstractTmpRecipe, self).__init__(
            corpus_dir, recipe_dir, verbose=verbose,
            log_file=os.path.join(self.output_dir, self.name + '.log'))

    def __del__(self):
        try:
            if self.delete_tmp:
                self.log.debug('removing recipe directory {}'
                               .format(self.to_delete))
                utils.remove(self.to_delete)
        except AttributeError:
            pass
