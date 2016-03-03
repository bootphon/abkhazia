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
# along with abkahzia. If not, see <http://www.gnu.org/licenses/>.
"""Provides the AbstractRecipe class"""

import os
import subprocess

import abkhazia.utils as utils
import abkhazia.kaldi.abkhazia2kaldi as abkhazia2kaldi


class AbstractRecipe(object):
    """A base class for creating kaldi recipes from an abkahzia corpus"""
    name = NotImplemented
    """The recipe's name"""

    params = NotImplemented
    """A named tuple defining the recipe parameters"""

    def __init__(self, corpus_dir, recipe_dir=None, verbose=False):
        # check corpus_dir
        if not os.path.isdir(corpus_dir):
            raise IOError("directory doesn't exist: {}".format(corpus_dir))
        self.corpus_dir = corpus_dir

        # init the log
        recipe_dir = self.corpus_dir if recipe_dir is None else recipe_dir
        log_file = os.path.join(recipe_dir, 'logs', self.name + '.log')
        log_dir = os.path.dirname(log_file)
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        self.log = utils.log2file.get_log(log_file, verbose)

        # check recipe_dir
        recipe_dir = os.path.join(recipe_dir, self.name, 's5')
        self.recipe_dir = recipe_dir

        if os.path.isdir(self.recipe_dir):
            raise OSError(
                'output directory already existing: {}'
                .format(self.recipe_dir))
        else:
            os.makedirs(self.recipe_dir)

        # init the abkhazia2kaldi converter
        self.a2k = abkhazia2kaldi.Abkhazia2Kaldi(
            corpus_dir, recipe_dir, verbose, self.log)

    def create(self, args):
        """Create the recipe in `self.recipe_dir`

        This method is abstract and must be implemented in child
        classes.

        args : an instance of self.params

        """
        raise NotImplementedError

    def run(self):
        """Run the created recipe by executing 'run.sh'"""
        # TODO catch failures
        self.log.info("running 'run.sh' from {}".format(self.recipe_dir))
        try:
            subprocess.check_call('./run.sh', cwd=self.recipe_dir)
        except subprocess.CalledProcessError:
            raise IOError('{} recipe failed'.format(self.name))
