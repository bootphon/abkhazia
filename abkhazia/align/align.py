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
"""Provides the Align and AlignNoLattice classes

Compute phone or word level forced alignment on an abkhazia corpus,
given features, a language model and an acoutic model.

The Align class lies on the 'wsj/steps/align_fmllr_lats.sh' kaldi
recipe, alignment is the 1best path on the generated lattice.

The AlignNolattice lies on the 'wsj/steps/align_fmllr.sh' kaldi recipe
where the alignment is computed directly on the GMM. This is faster
but doesn't allow to retrieve posterior probabilities of the aligned
phones.

Note that some timestamps and missing/added silences can differ in the
two alignment recipes, the Align recipe seems to add more silences.

"""

import gzip
import os
import shutil
import operator
import time
import numpy as np
import abkhazia.utils as utils
import abkhazia.abstract_recipe as abstract_recipe
from abkhazia.utils.best_path_dtw import dtw
from collections import defaultdict
from operator import itemgetter
from abkhazia.language import check_language_model, read_int2phone
from abkhazia.acoustic import check_acoustic_model
from abkhazia.features import Features

from joblib import Parallel, delayed


# TODO check alignment: which utt have been transcribed, have silence
# been inserted, otherwise no difference? (maybe some did not reach
# final state), chronological order, grouping by utt_id etc.
class Align(abstract_recipe.AbstractRecipe):
    """Estimate forced alignment of an abkahzia corpus"""
    name = 'align'

    _align_script = 'steps/align_fmllr_lats.sh'
    """The alignment recipe in Kaldi"""

    def __init__(self, corpus, output_dir=None,
                 log=utils.logger.null_logger()):
        super(Align, self).__init__(corpus, output_dir, log=log)

        # features, language and acoustic models directories
        self.feat_dir = None
        self.lm_dir = None
        self.am_dir = None

        # alignment parameters
        self.level = 'both'  # 'both', 'words' or 'phones'
        self.acoustic_scale = 0.1
        self.with_posteriors = False

    def check_parameters(self):
        super(Align, self).check_parameters()
        self._check_level()
        self._check_with_posteriors()
        self._check_acoustic_scale()

        check_acoustic_model(self.am_dir)
        check_language_model(self.lm_dir)

        self.meta.source += (', feat = {}, lm = {}, am = {}'.format(
            self.feat_dir, self.lm_dir, self.am_dir))

    def create(self):
        super(Align, self).create()

        # copy features scp files in the recipe_dir
        Features.export_features(
            self.feat_dir,
            os.path.join(self.recipe_dir, 'data', self.name))

    def run(self):
        # build alignment lattice
        self._align_fmllr()

        # extract phone level best path
        self._best_path()
        self._ali_to_phones()

        # extract posteriors if asked
        if self.with_posteriors:
            self._post_to_phones()

    def export(self):
        int2phone = read_int2phone(self.lm_dir)
        ali = self._read_result_utts('ali')
        post = self._read_result_utts('post') if self.with_posteriors else None

        # retrieve the export function according to `level`
        func = {'phones': self._export_phones,
                'words': self._export_words,
                'both': self._export_phones_and_words}[self.level]
        aligned = func(int2phone, ali, post)

        # write it to the target file
        target = os.path.join(self.output_dir, 'alignment.txt')
        with utils.open_utf8(target, 'w') as out:
            for line in aligned:
                out.write(line.strip() + '\n')

        super(Align, self).export()

    def _check_level(self):
        """Raise IOError on bad alignment level"""
        if self.level not in ['both', 'words', 'phones']:
            raise IOError("alignment level must be in 'phones', 'words' or "
                          "'both', it is '{}'".format(self.level))

    def _check_with_posteriors(self):
        """Force with_posteriors to False if it's not a bool"""
        if not isinstance(self.with_posteriors, bool):
            self.log.warning(
                'alignment posteriors flag is not a bool, forcing to False')
            self.with_posteriors = False

    def _check_acoustic_scale(self):
        """Raise IOError if acoustic_scale not a float"""
        if not isinstance(self.acoustic_scale, float):
            raise IOError('acoustic scale must be a float, it is {}'
                          .format(type(self.acoustic_scale)))

    def _target_dir(self):
        """Return the directory where to put kaldi results

        The directory is created empty if not existing

        """
        target = os.path.join(self.recipe_dir, 'exp', 'align_fmllr')
        if not os.path.isdir(target):
            os.makedirs(target)
        return target

    def _align_fmllr(self):
        """Run the alignment script from kaldi recipe"""
        self.log.info('computing fMLLR alignment lattice')
        self._run_command(
            self._align_script + ' --nj {0} --cmd "{1}" {2} {3} {4} {5}'
            .format(
                self.njobs,
                utils.config.get('kaldi', 'train-cmd'),
                os.path.join(self.recipe_dir, 'data', 'align'),
                self.lm_dir,
                self.am_dir,
                self._target_dir()))

    def _best_path(self):
        """Run lattice-best-path Kaldi binary

        Read _target_dir/lat.*.gz, write _target_dir/{best, tra}.*.gz

        """
        self.log.info('extracting best path in lattice')
        self._run_command(
            '{0} JOB=1:{1} {2}/log/best_path.JOB.log '
            'lattice-best-path --acoustic-scale={3} '
            '"ark:gunzip -c {2}/lat.JOB.gz|" "ark:|gzip -c >{2}/tra.JOB.gz" '
            '"ark:|gzip -c >{2}/best.JOB.gz"'.format(
                os.path.join('utils', utils.config.get('kaldi', 'train-cmd')),
                self.njobs,
                self._target_dir(),
                self.acoustic_scale))

    def _ali_to_phones(self):
        """Run ali-to-phones Kaldi binary

        Read _target_dir/{best.*.gz, final.mdl}, write _target_dir/ali.*.gz

        """
        self.log.info('aligning best path to phones')
        self._run_command(
            '{0} JOB=1:{1} {2}/log/ali-to-phones.JOB.log '
            'ali-to-phones --write_lengths=true {3} '
            '"ark:gunzip -c {2}/best.JOB.gz|" '
            '"ark,t:|gzip -c >{2}/ali.JOB.gz"'.format(
                os.path.join('utils', utils.config.get('kaldi', 'train-cmd')),
                self.njobs,
                self._target_dir(),
                os.path.join(self._target_dir(), 'final.mdl')))

    def _post_to_phones(self):
        """Compute alignment posteriors from lattice best path

        Read _target_dir/{best, lat}.*.gz, write _target_dir/post.*.gz

        """
        self.log.info('extracting alignment posterior probabilities')

        # First we need to rerun ali-to-phones with the --per-frame
        # option. If this appears to slow, we can optimize with only
        # one call to ali-phone and a custom conversion frame -> phone
        # (in this case be carefull not to loose word boundaries).
        self._run_command(
            '{0} JOB=1:{1} {2}/log/frame-ali-to-phones.JOB.log '
            'ali-to-phones --per-frame=true {3} '
            '"ark:gunzip -c {2}/best.JOB.gz|" '
            '"ark:|gzip -c >{2}/frame_ali.JOB.gz"'.format(
                os.path.join('utils', utils.config.get('kaldi', 'train-cmd')),
                self.njobs,
                self._target_dir(),
                os.path.join(self._target_dir(), 'final.mdl')))

        self._run_command(
            '{0} JOB=1:{1} {2}/log/post-on-ali.JOB.log '
            'lattice-to-post --acoustic-scale={3} '
            '"ark:gunzip -c {2}/lat.JOB.gz|" ark:- | '
            'post-to-phone-post {4} ark:- ark:- | '
            'get-post-on-ali ark:- "ark:gunzip -c {2}/frame_ali.JOB.gz|" '
            '"ark,t:|gzip -c >{2}/post.JOB.gz"'.format(
                os.path.join('utils', utils.config.get('kaldi', 'train-cmd')),
                self.njobs,
                self._target_dir(),
                self.acoustic_scale,
                os.path.join(self._target_dir(), 'final.mdl')))

    def _read_result_utts(self, start):
        """Read kaldi output files as utt_ids indexed dict

        read from _target_dir/start.*.gz, return a dict[utt-id] ->
        file content.

        """
        path = self._target_dir()
        data = []
        for _file in sorted(
                [os.path.join(path, f) for f in os.listdir(path)
                 if f.startswith(start)]):
            data += gzip.open(_file, 'r').readlines()

        return {line[0]: ' '.join(line[1:]) for line in
                (l.replace('[', '').replace(']', '').split() for l in data)}

    @staticmethod
    def _read_alignment(phonemap, ali, post):
        """Tokenize raw kaldi alignment output"""
        for utt_id, line in ali.iteritems():
            # TODO make this a parameter (with the 0.01 above), or
            # read it from the features instance. This is the center
            # time of the first window, as specified when computing
            # the features.
            start = 0.0125

            if post:
                utt_post = [float(p) for p in post[utt_id].split()]

            for pair in line.strip().split(' ; '):
                code, nframes = pair.split(' ')
                nframes = int(nframes)
                stop = start + 0.01*nframes

                if post:
                    mpost = sum(utt_post[:nframes]) / nframes
                    utt_post = utt_post[nframes:]
                    yield (utt_id, str(start), str(stop),
                           str(mpost), phonemap[code])
                else:
                    yield (utt_id, str(start), str(stop), phonemap[code])

                start = stop

    @staticmethod
    def _read_splited(path):
        """Read lines from a file, each line being striped and split"""
        lines = path if isinstance(path, list) else utils.open_utf8(path, 'r')
        return (l.strip().split() for l in lines)

    @classmethod
    def _read_utts(cls, path):
        """Yield utterances as pairs (utt_id, alignment) from alignment file"""
        utt_id = None
        alignment = []
        for line in cls._read_splited(path):
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

    @classmethod
    def _read_words(cls, path):
        """Yield words alignement from a 'phone and words' alignment file"""
        word = None
        utt_id = None
        start = 0
        stop = 0
        for line in cls._read_splited(path):
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

    def _export_phones(self, int2phone, ali, post):
        """Export alignment at phone level"""
        return [' '.join(seq) for seq
                in self._read_alignment(int2phone, ali, post)]

    def _export_phones_and_words(self, int2phone, ali, post):
        """Export alignment at both phone and word levels"""
        # phone level alignment
        phones = self._export_phones(int2phone, ali, post)

        # text[utt_id] = list of words
        text = {k: v.strip().split()
                for k, v in self.corpus.text.iteritems()}

        # lexicon[word] = list of phones
        lexicon = {k: v.strip().split()
                   for k, v in self.corpus.lexicon.iteritems()}

        words = []

        t0=time.time()
        #try:
        utts = [(utt_id, utt_align) for utt_id, utt_align in self._read_utts(phones)]

        list_phones = defaultdict(list)
        word_pos = defaultdict(list)
        utt_alignment = [aligned.split(' ')[-1] for aligned in utt_align]

        # create list of all the phones using the lexicon
        for word in text[utt_id]:
            try:
                list_phones[utt_id] += lexicon[word]
                word_pos[utt_id] += [word] * len(lexicon[word])
            except KeyError:
                continue

        try:
            for utt_id, utt_align in self._read_utts(phones):
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

                    while wlen > 0 and idx<len(utt_align):
                        aligned = utt_align[idx]
                        if aligned.split()[-1] in self.corpus.silences:
                            words.append('{}'.format(aligned))
                        else:
                            words.append('{} {}'.format(
                                aligned, word if begin else ''))
                            wlen -= 1
                            begin = False
                        idx += 1
        except IndexError:
            Parallel(self.njobs)(
                delayed(dtw)([aligned.split(' ')[-1]
                                          for aligned in utt_align],
                                          list_phones[utt_id],
                                          word_pos[utt_id], utt_align)
                                         for utt_id, utt_align in utts)
            t1=time.time()
            print "dtw took",t1-t0
        return words

    def _export_words(self, int2phone, ali, post):
        """Export alignment at word level only"""
        return [w for w in self._read_words(
            self._export_phones_and_words(int2phone, ali, post))]
    
    @staticmethod
    def phone_word_dtw(self, utt_align, text):
        """ Get the word level alignment from the phone level
            alignment and the lexicon """
        lexicon = {k: v.strip().split()
                   for k, v in self.corpus.lexicon.iteritems()}

        list_phones = []
        word_pos = []
        word_alignment = []
        alignment = [aligned.split(' ')[-1] for aligned in utt_align]

        # create list of all the phones using the lexicon
        for word in text:
            try:
                list_phones += lexicon[word]
                word_pos += [word] * len(lexicon[word])
            except KeyError:
                continue

        # init dtw matrix
        dtw = np.zeros((len(alignment),len(list_phones)))
        dtw[0,:] = np.inf
        dtw[:,0] = np.inf
        dtw[0,0] = 0

        # compute dtw costs
        for i in range(1,len(alignment)):
            for j in range(1,len(list_phones)):
                cost = int(not alignment[i] == list_phones[j])
                dtw[i,j] = cost + min([dtw[i-1,j], dtw[i,j-1], dtw[i-1, j-1]])
        word_alignment.append(word_pos[-1])

        # go backward to get the best path
        i = len(alignment) - 1
        j = len(list_phones) - 1
        path = []
        while (not i == 0 and not j == 0):
            options = [dtw[i-1,j], dtw[i,j-1], dtw[i-1, j-1]]
            idx, val = min(enumerate(options), key=itemgetter(1))
            if idx == 0:
                i = i-1
                word_alignment.append(word_pos[j])
                path.append((i,j,word_pos[j]))
                continue
            elif idx == 1:
                word_alignment.pop()
                word_alignment.append(word_pos[j-1])
                j = j-1
                path.append((i,j,word_pos[j]))
                continue
            elif idx == 2:
                word_alignment.append(word_pos[j-1])
                i = i-1
                j = j-1
                path.append((i,j,word_pos[j]))
                continue

        # return alignment with words
        word_alignment.reverse()

        prev_word = ''
        complete_alignment = []
        for utt,word in zip(utt_align, word_alignment):
            if word == prev_word:
                prev_word = word
                complete_alignment.append(utt)
                continue
            else:
                prev_word = word
                complete_alignment.append(u'{} {}'.format(utt,word))

        #complete_alignment = ['{} {}'.format(utt,word)
        #        for utt, word in zip(utt_align,word_alignment)]
        return complete_alignment


class AlignNoLattice(Align):
    """Estimate forced alignment of an abkahzia corpus"""
    _align_script = 'steps/align_fmllr.sh'

    def _check_with_posteriors(self):
        """Force with_posteriors to False"""
        if self.with_posteriors is not False:
            self.log.warning(
                'posteriors are only available on lattice based alignment')
            self.with_posteriors = False

    def run(self):
        self._align_fmllr()

        # the previous script output ali.*.gz instead of lats.*.gz, rename
        # them in best.*.gz (conform to what the ali_to_phone method expect)
        path = self._target_dir()
        for ali_file in (f for f in os.listdir(path) if f.startswith('ali.')):
            shutil.move(
                os.path.join(path, ali_file),
                os.path.join(path, ali_file.replace('ali', 'best')))

        self._ali_to_phones()


def utterances_posterior_scoring(alignment_file, score_fun=np.prod):
    """Estimate a score for each utterance based on posteriograms

    For each utterances, extracts all its posteriors as a list of
    floats and apply the function `score_fun` to it.

    :param alignmement_file: The path to an alignment file with
      posteriors.  Each line in the must must be: "utt-id tstart tstop
      posterior phone [word]", we consider only column 1 and column 4.

    :param score_fun: any function (list of floats) -> float

    :return: a generator of (utt-id, score) returning the obtained
      score for each utterance defined in the alignment file.

    """
    for utt, alignment in Align._read_utts(alignment_file):
        posteriors = [float(line.split(' ')[3]) for line in alignment]
        yield utt, score_fun(posteriors)
