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

import abkhazia.core.abstract_recipe as abstract_recipe
import abkhazia.core.kaldi2abkhazia as k2a
import abkhazia.utils as utils
from abkhazia.core.language_model import check_language_model
from abkhazia.core.acoustic_model import check_acoustic_model
from abkhazia.core.features import export_features


def _read_splited(f):
    """Read lines from a file, each line being striped and split"""
    return (l.strip().split() for l in utils.open_utf8(f, 'r'))


def _read_utts(f):
    """Yield utterances as tuples (utt_id, alignment) from an alignment file"""
    utt_id = None
    alignment = []
    for line in _read_splited(f):
        if utt_id is None:
            utt_id = line[0]
            alignment.append(' '.join(line))
        elif line[0] != utt_id and alignment != []:
            yield utt_id, alignment
            utt_id = line[0]
            alignment = [' '.join(line)]
        else:
            alignment.append(' '.join(line))
    yield utt_id, alignment


def _append_words_to_alignment(ftext, flexicon, falignment, foutput, log):
    """Append words to phone lines in the final alignment file"""
    # text[utt_id] = list of words
    text = dict((l[0], l[1:]) for l in _read_splited(ftext))

    # lexicon[word] = list of phones
    lexicon = dict((l[0], l[1:]) for l in _read_splited(flexicon))

    with utils.open_utf8(foutput, 'w') as out:
        for utt_id, utt_align in _read_utts(falignment):
            idx = 0
            for word in text[utt_id]:
                begin = True
                try:
                    for phone in lexicon[word]:
                        out.write('{} {}\n'.format(
                            utt_align[idx], word if begin else ''))
                        idx += 1
                        begin = False
                except KeyError:  # the word isn't in lexicon
                    log.debug('ignoring out of lexicon word: %s', word)


class ForceAlign(abstract_recipe.AbstractTmpRecipe):
    """Compute forced alignment of an abkhazia corpus

    Takes a corpus in abkhazia format and instantiates a kaldi recipe
    to train a standard speaker-adapted triphone HMM-GMM model on the
    whole corpus and generate a forced alignment.

    """
    name = 'align'

    def __init__(self, corpus_dir, output_dir=None, verbose=False):
        super(ForceAlign, self).__init__(corpus_dir, output_dir, verbose)

        # language and acoustic models directories
        self.lm_dir = None
        self.feat_dir = None
        self.am_dir = None

    def _align_fmllr(self):
        self.log.info('computing forced alignment')

        target = os.path.join(self.recipe_dir, 'exp', 'ali_fmllr')
        if not os.path.isdir(target):
            os.makedirs(target)

        self._run_command(
            'steps/align_fmllr.sh --nj {0} --cmd "{1}" {2} {3} {4} {5}'
            .format(
                self.njobs,
                utils.config.get('kaldi', 'train-cmd'),
                os.path.join(self.recipe_dir, 'data', 'align'),
                self.lm_dir,
                self.am_dir,
                target))

    def _ali_to_phones(self):
        self.log.info('exporting to phone alignment')

        export = os.path.join(self.recipe_dir, 'export')
        target = os.path.join(export, 'forced_alignment.tra')
        if not os.path.isdir(export):
            os.makedirs(export)

        self._run_command(
            'ali-to-phones --write_lengths=true {0}'
            ' "ark,t:gunzip -c {1}|" ark,t:{2}'.format(
                os.path.join(self.am_dir, 'final.mdl'),
                os.path.join(self.recipe_dir, 'exp', 'ali_fmllr', 'ali.*.gz'),
                target))

        # if we want to use the tri2a results directly without the final
        # forced alignment (is there any difference between the two beyond one
        # being done using only one job?)
        # ali-to-phones \
        #     --write_lengths=true exp/tri2a/final.mdl \
        #     "ark,t:gunzip -c exp/tri2a/ali.*.gz|" \
        #     ark,t:export/forced_alignment.tra

    def check_parameters(self):
        super(ForceAlign, self).check_parameters()
        check_acoustic_model(self.am_dir)
        check_language_model(self.lm_dir)

    def create(self):
        """Create the recipe data in `self.recipe_dir`"""
        super(ForceAlign, self).create()

        # setup scp files from the features directory in the recipe dir
        export_features(
            self.feat_dir,
            os.path.join(self.recipe_dir, 'data', self.name),
            self.corpus_dir)

    def run(self):
        self._align_fmllr()
        self._ali_to_phones()

    def export(self, words=True):
        """Export the kaldi tra alignment file in abkhazia format

        This method reads data/lang/phones.txt and
        export/forced_aligment.tra and write
        export/forced_aligment.txt

        If words is True, append entire words to the alignment.

        """
        target = os.path.join(self.output_dir, 'alignment.txt')

        tra = os.path.join(self.recipe_dir, 'export', 'forced_alignment.tra')
        k2a.export_phone_alignment(
            os.path.join(self.lm_dir, 'phones.txt'),
            tra, tra.replace('.tra', '.tmp' if words else '.txt'))

        # append complete words to the list of aligned phones
        if words:
            _append_words_to_alignment(
                os.path.join(self.corpus_dir, 'data', 'text.txt'),
                os.path.join(self.corpus_dir, 'data', 'lexicon.txt'),
                tra.replace('.tra', '.tmp'),
                target,
                self.log)
            utils.remove(tra.replace('.tra', '.tmp'))

        super(ForceAlign, self).export()
