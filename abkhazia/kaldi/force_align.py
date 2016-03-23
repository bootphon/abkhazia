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
"""Provides the ForceAlign class"""

import os

import abkhazia.kaldi.abstract_recipe as abstract_recipe
import abkhazia.kaldi.kaldi2abkhazia as k2a


class ForceAlign(abstract_recipe.AbstractRecipe):
    """Compute forced alignment of an abkhazia corpus

    Takes a corpus in abkhazia format and instantiates a kaldi recipe
    to train a standard speaker-adapted triphone HMM-GMM model on the
    whole corpus and generate a forced alignment.

    """
    name = 'align'

    def create(self, args):
        # setup data files. Those files are linked from the acoustic
        # model recipe instead of being prepared from the corpus data.
        target_dir = os.path.join(self.recipe_dir, 'data/align')
        os.makedirs(target_dir)
        for source in ('text', 'utt2spk', 'spk2utt', 'segments',
                       'wav.scp', 'feats.scp', 'cmvn.scp'):
            origin = os.path.abspath(os.path.join(
                args.acoustic, '../../data/acoustic', source))
            if os.path.isfile(origin):
                target = os.path.join(target_dir, source)
                os.link(origin, target)
            else:
                self.log.debug('no such file %s', origin)

        # setup other files and folders
        self.a2k.setup_kaldi_folders()
        self.a2k.setup_machine_specific_scripts()
        self.a2k.setup_score()
        self.a2k.setup_run('force_align.sh.in', args)

    def export(self, args):
        """Export the kaldi tra alignment file in abkhazia format

        This method reads data/lang/phones.txt and
        export/forced_aligment.tra and write
        export/forced_aligment.txt

        """
        tra = os.path.join(self.recipe_dir, 'export', 'forced_alignment.tra')
        k2a.export_phone_alignment(
            os.path.join(args.lang, 'phones.txt'),
            tra, tra.replace('.tra', '.txt'))
