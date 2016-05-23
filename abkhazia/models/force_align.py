# coding: utf-8

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

import abkhazia.utils as utils
import abkhazia.models.abstract_recipe as abstract_recipe
from abkhazia.models.language_model import check_language_model
from abkhazia.models.acoustic_model import check_acoustic_model
from abkhazia.models.features import export_features


def _read_splited(f):
    """Read lines from a file, each line being striped and split"""
    lines = f if isinstance(f, list) else utils.open_utf8(f, 'r')
    return (l.strip().split() for l in lines)


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


def _read_words(f):
    """Yield words alignement from a 'phone and words' alignment file"""
    word = None
    utt_id = None
    start = 0
    stop = 0
    for line in _read_splited(f):
        if len(line) == 5:  # new word
            if word is not None:
                yield ' '.join([utt_id, start, stop, word])
            word = line[4]
            utt_id = line[0]
            start = line[1]
            stop = line[2]
        else:  # word continues
            stop = line[2]
    if word is not None:
        yield ' '.join([utt_id, start, stop, word])


def _read_int2phone(phone2int, word_position_dependent=True):
    """Return int2phones from the `phone2int` file"""
    phonemap = {}
    for line in utils.open_utf8(phone2int, 'r').xreadlines():
        phone, code = line.strip().split(u" ")
        # remove word position markers
        if word_position_dependent and phone[-2:] in ['_I', '_B', '_E', '_S']:
            phone = phone[:-2]
        phonemap[code] = phone
    return phonemap


def _read_tra_alignment(phonemap, tra):
    # tra_file using the format on each line: utt_id [phone_code
    # n_frames]+ this is a generator (it yields in the loop)
    for line in utils.open_utf8(tra, 'r'):
        sequence = line.strip().split(u" ; ")
        utt_id, code, nframes = sequence[0].split(u" ")
        sequence = [u" ".join([code, nframes])] + sequence[1:]
        # this seems good enough, but I (Thomas) didn't check in the
        # make_mfcc code of kaldi to be sure
        start = 0.0125

        for elem in sequence:
            code, nframes = elem.split(u" ")
            stop = start + 0.01*int(nframes)
            yield (utt_id, str(start), str(stop), phonemap[code])
            start = stop


class ForceAlign(abstract_recipe.AbstractRecipe):
    """Compute forced alignment of an abkhazia corpus

    Takes a corpus in abkhazia format and instantiates a kaldi recipe
    to train a standard speaker-adapted triphone HMM-GMM model on the
    whole corpus and generate a forced alignment.

    """
    name = 'align'

    def __init__(self, corpus, output_dir=None, log=utils.null_logger()):
        super(ForceAlign, self).__init__(corpus, output_dir, log=log)

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

        self.meta.source += (', feat = {}, lm = {}, am = {}'.format(
            self.feat_dir, self.lm_dir, self.am_dir))

    def create(self):
        """Create the recipe data in `self.recipe_dir`"""
        super(ForceAlign, self).create()

        # setup scp files from the features directory in the recipe dir
        export_features(
            self.feat_dir,
            os.path.join(self.recipe_dir, 'data', self.name),
            self.corpus)

    def run(self):
        self._align_fmllr()
        self._ali_to_phones()

    # TODO check alignment: which utt have been transcribed, have silence
    # been inserted, otherwise no difference? (maybe some did not reach
    # final state), chronological order, grouping by utt_id etc.
    @staticmethod
    def _export_phones(int2phone, tra):
        return [' '.join([utt_id, start, stop, phone])
                for utt_id, start, stop, phone
                in _read_tra_alignment(int2phone, tra)]

    def _export_phones_and_words(self, int2phone, tra):
        # phone level alignment
        phones = self._export_phones(int2phone, tra)

        # text[utt_id] = list of words
        text = {k: v.strip().split()
                for k, v in self.corpus.text.iteritems()}

        # lexicon[word] = list of phones
        lexicon = {k: v.strip().split()
                   for k, v in self.corpus.lexicon.iteritems()}

        words = []
        for utt_id, utt_align in _read_utts(phones):
            idx = 0
            # for each word in transcription, parse it's aligned
            # phones and add the word after the first phone belonging
            # to that word.
            for word in text[utt_id]:
                try:
                    wlen = len(lexicon[word])
                except KeyError:  # the word isn't in lexicon
                    self.log.warning(
                        'ignoring out of lexicon word: %s', word)

                # from idx, we eat wlen phones (+ any silence phone)
                begin = True
                while wlen > 0:
                    aligned = utt_align[idx]
                    if aligned.split()[-1] in self.corpus.silences:
                        words.append('{}'.format(aligned))
                    else:
                        words.append('{} {}'.format(
                            aligned, word if begin else ''))
                        wlen -= 1
                        begin = False
                    idx += 1
        return words

    def _export_words(self, int2phone, tra):
        w_and_p = self._export_phones_and_words(int2phone, tra)
        return [w for w in _read_words(w_and_p)]

    def export(self, level='both'):
        """Export the kaldi tra alignment file in abkhazia format

        This method reads data/lang/phones.txt and
        export/forced_aligment.tra and write
        export/forced_aligment.txt

        level (str): level must be in ['words', 'phones', 'both'],
          default is 'both'

        """
        if level not in ('both', 'words', 'phones'):
            raise IOError('unknown alignment level {}'.format(level))

        tra = os.path.join(self.recipe_dir, 'export', 'forced_alignment.tra')
        int2phone = _read_int2phone(os.path.join(self.lm_dir, 'phones.txt'))

        # retrieve the export function according to `level`
        func = {'phones': self._export_phones,
                'words': self._export_words,
                'both': self._export_phones_and_words}[level]
        aligned = func(int2phone, tra)

        # write it to the target file
        target = os.path.join(self.output_dir, 'alignment.txt')
        with utils.open_utf8(target, 'w') as out:
            for line in aligned:
                out.write(line.strip() + '\n')

        super(ForceAlign, self).export()
