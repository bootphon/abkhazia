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
"""Implementation of the 'abkazia plot' command"""

import os

from abkhazia.commands.abstract_command import AbstractCoreCommand
from abkhazia.corpus import Corpus
import abkhazia.utils as utils


class AbkhaziaPlot(AbstractCoreCommand):
    '''This class implements the 'abkhazia plot' command'''
    name = 'plot'
    description = 'Plot the speech duration distribution of the corpus'

    @classmethod
    def run(cls, args):
        corpus_dir, output_dir = cls._parse_io_dirs(args)
        log = utils.logger.get_log(
            os.path.join(output_dir, 'filter.log'), verbose=args.verbose)

        corpus = Corpus.load(corpus_dir, validate=args.validate, log=log)
        
        corpus_plot = corpus.plot()

        corpus_plot.show()
        
