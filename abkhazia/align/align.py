# Copyright 2016-2018 Thomas Schatz, Xuan-Nga Cao, Mathieu Bernard
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
import numpy as np

import abkhazia.utils as utils
import abkhazia.abstract_recipe as abstract_recipe

from abkhazia.language import check_language_model, read_int2phone
from abkhazia.features import Features


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

        # late import to avoid circular import (align imports acoustic
        # for the convert_alignment_to_kaldi_format function)
        from abkhazia.acoustic import check_acoustic_model
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
            out.write('\n'.join(line.strip() for line in aligned) + '\n')

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

        if self.level == 'words' and self.with_posteriors:
            raise NotImplementedError(
                'cannot compute words alignment with posteriors')

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
            '{cmd} JOB=1:{njobs} {dir}/log/best_path.JOB.log '
            'lattice-best-path --acoustic-scale={scale} '
            '"ark:gunzip -c {dir}/lat.JOB.gz|" '
            '"ark:|gzip -c >{dir}/tra.JOB.gz" '
            '"ark:|gzip -c >{dir}/best.JOB.gz"'.format(
                cmd=os.path.join(
                    'utils', utils.config.get('kaldi', 'train-cmd')),
                njobs=self.njobs,
                dir=self._target_dir(),
                scale=self.acoustic_scale))

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
            data += [l.decode() for l in gzip.open(_file, 'r')]

        return {line[0]: ' '.join(line[1:]) for line in
                (l.replace('[', '').replace(']', '').split() for l in data)}

    @staticmethod
    def _read_alignment(
            phonemap, ali, post,
            first_frame_center_time=.0125,
            frame_width=0.025, frame_spacing=0.01):
        """Tokenize raw kaldi alignment output"""
        for utt_id, line in ali.items():
            start = first_frame_center_time - frame_width / 2.0
            current_frame_center_time = first_frame_center_time

            if post:
                utt_post = [float(p) for p in post[utt_id].split()]

            pairs = line.strip().split(' ; ')
            nb_pairs = len(pairs)
            for i, pair in enumerate(pairs):
                code, nframes = pair.split(' ')
                nframes = int(nframes)
                if i == nb_pairs - 1:
                    # last phone
                    stop = (current_frame_center_time
                            + frame_spacing * (nframes - 1.0)
                            + frame_width / 2.0)
                    current_frame_center_time = None
                else:
                    stop = (current_frame_center_time
                            + frame_spacing * (nframes - 0.5))
                    current_frame_center_time = stop + 0.5 * frame_spacing

                if post:
                    mpost = sum(utt_post[:nframes]) / nframes
                    utt_post = utt_post[nframes:]
                    yield (
                        utt_id,
                        '{:.4f}'.format(start),
                        '{:.4f}'.format(stop),
                        '{:.4f}'.format(mpost),
                        phonemap[code])
                else:
                    yield (
                        utt_id,
                        '{:.4f}'.format(start),
                        '{:.4f}'.format(stop),
                        phonemap[code])

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

    def _read_words(self, path):
        """Yield words alignement from a 'phone and words' alignment file"""
        word = None
        start = 0
        stop = 0
        for utt_id, alignment in self._read_utts(path):
            for line in self._read_splited(alignment):
                phone = line[3]
                if len(line) == 5:  # new word
                    if word is not None:
                        yield ' '.join([utt_id, start, stop, word])
                    word = line[4]
                    # utt_id = line[0]
                    start = line[1]
                    stop = line[2]
                elif (phone in self.corpus.silences): 
                    # Don't count SIL as part of the word
                    continue
                else:  # word continues
                    stop = line[2]

            if word is not None:
                yield ' '.join([utt_id, start, stop, word])
                word = None

    def _export_phones(self, int2phone, ali, post):
        """Export alignment at phone level"""
        return [' '.join(seq) for seq
                in self._read_alignment(int2phone, ali, post)]

    def _export_phones_and_words(self, int2phones, ali, post):
        """Export alignment at both phone and word levels"""
        phones_alignment = self._export_phones(int2phones, ali, post)

        # align the words on the phones, utterance by utterance
        alignment = []
        for utt_id, utt_align in self._read_utts(phones_alignment):
            alignment += self._align_utterance(utt_id, utt_align)
        return alignment

    def _align_utterance(self, utt_id, utt_align):
        # the words we have to align in the utterance
        words = self.corpus.text[utt_id].strip().split()

        # align the utterance word by word
        index = 0
        for word in words:
            try:
                utt_align, index = self._align_word(word, utt_align, index)
            except IndexError:
                self.log.warning(
                    f'failed to align words from phones on utterance {utt_id}: '
                    f'phones dont match word')
            except KeyError as err:
                self.log.warning(
                    f'failed to align words from phones on utterance {utt_id}: '
                    f'{str(err)}')


        return utt_align

    def _align_word(self, word, alignment, index):
        # the word cut in phones
        try:
            phones = self.corpus.lexicon[word].strip().split()
        except KeyError:
            raise KeyError(f'out-of-vocabulary word: {word}')

        for n, phone in enumerate(phones):
            index = self._align_phone(phone, alignment, index)
            if n == 0:
                alignment[index] += f' {word}'

        # go to next phone, in case next word starts with same
        # phone
        index += 1

        return alignment, index

    @staticmethod
    def _align_phone(phone, alignment, index):
        current_phone = alignment[index].strip().split()[-1]

        while phone != current_phone:
            index += 1
            current_phone = alignment[index].strip().split()[-1]
        return index

    def _export_words(self, int2phone, ali, post):
        """Export alignment at word level only"""
        return [w for w in self._read_words(
            self._export_phones_and_words(int2phone, ali, post))]


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


def yield_on_words(alignment):
    """Yield words as lists of (tstart, tstop, phone, [word])

    Parameters
    ----------
    alignment : list of [tstart, tstop, phone, [word]]

    Yields
    ------
    A list of [tstart, tstop, phone, [word]] per word in `alignment`.

    """
    word = []
    for phone in alignment:
        if len(phone) == 4:
            if word:
                yield word
                word = []
        word.append(phone)
    yield word


def convert_to_word_position_dependent(alignment):
    """Add the position dependent suffixes to phones in `alignment`"""
    wpd_alignment = {}

    for utt, utt_phones in alignment.items():
        utt_phones_wpd = []
        # iterate by words
        for word in yield_on_words(utt_phones):
            lex = [p[2] for p in word]
            if len(lex) == 1:
                lex = [lex[0] + '_S']  # single phone word
            else:
                lex = (
                    [lex[0] + '_B'] +  # first phone in word
                    [l + '_I' for l in lex[1:-1]] +  # intermediate phones
                    [lex[-1] + '_E'])  # last phone

            word_wpd = []
            for i, p in enumerate(word):
                pp = [p[0], p[1], lex[i]]
                if len(p) == 4:
                    pp.append(p[3])
                word_wpd.append(pp)

            utt_phones_wpd += word_wpd

        wpd_alignment[utt] = utt_phones_wpd

    return wpd_alignment


def convert_alignment_to_kaldi_format(
        input_ali_file, lang_dir, wpd=False,
        frame_width=0.025, frame_spacing=0.01, log=utils.logger.get_log()):
    """Convert an alignment file from abkhazia format to kaldi format

    Parameters
    ----------
    input_ali_file : file
        The original alignment file in abkhazia format
    lang_dir : dircetory
        The 'lang' directory asgenerated by Kaldi's prep_lang.sh script
    wpd : bool, optional
        True when dealing with word position dependant phones, default
        to False
    frame_width, frame_spacing : float, optional
        Depends on the features computed on the corpus used with the
        alignments. Default values are for default MFCC features.

    Returns
    -------
    The converted alignment as a dict of utterances

    Raises
    ------
    ValueError on issues

    """
    log.info('convert alignment to Kaldi format: %s', input_ali_file)
    phonemap_file = os.path.join(lang_dir, 'phones.txt')
    log.debug('... loading %s', phonemap_file)

    if not os.path.isfile(phonemap_file):
        raise ValueError('file not found: {}'.format(phonemap_file))

    # load the phonemap file as a dict {phone: int}
    phonemap = {}
    for line in utils.open_utf8(phonemap_file, 'r'):
        p, i = line.strip().split()
        phonemap[p] = i

    log.debug('... loading %s', input_ali_file)
    # for each utterance, a list of lists [tstart, tstop, phone, [word]]
    alignment = {utt: [a.split(' ')[1:] for a in ali]
                 for utt, ali in Align._read_utts(input_ali_file)}

    # if needed, convert the alignment phones to position dependent
    # ones (we append _B, _I, _E or _S to each phone)
    if wpd:
        log.debug('... adapting alignment to word position dependent phones')
        alignment = convert_to_word_position_dependent(alignment)

    # Critical part, converts a phone duration to a number of frames
    # in the features
    def frame_duration(tstart, tstop):
        return int(round(
            (float(tstop) - float(tstart)) / frame_spacing))

    def convert_phone(line):
        tstart = line[0]
        tstop = line[1]
        phone = line[2]

        try:
            p = phonemap[phone]
        except KeyError:
            raise ValueError(
                'phone {} not found in phonemap {}'
                .format(phone, phonemap_file))

        return ' '.join(p) * frame_duration(tstart, tstop)

    log.debug('... finally converting alignment to Kaldi format')
    out = {utt: ' '.join(convert_phone(phone))
           for utt, phones in alignment.items() for phone in phones}

    return out


def merge_phones_words_alignments(ali_phones, ali_words):
    """Merge two alignments at phone and word into a single one

    Phone alignment is at format "utt_id, tstart, tstop, phone".

    Word alignment is at format "utt_id, tstart, tstop, word".

    Merged alignment is at format "utt_id, tstart, tstop, phone [word]",
    where the word is specified only at the forst phone of that word.

    """
    for utt, phones in ali_phones.items():
        words = ali_words[utt]
        words_index = 0
        for n, (t, u, p) in enumerate(phones):
            if len(words) > words_index and words[words_index][0] == t:
                ali_phones[utt][n] = (t, u, p, words[words_index][2])
                words_index += 1
    return ali_phones
