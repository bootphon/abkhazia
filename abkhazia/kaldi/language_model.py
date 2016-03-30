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
"""Provides the LanguageModel class"""

import gzip
import os
import pkg_resources
import shutil
import tempfile

import abkhazia.utils as utils
import abkhazia.utils.basic_io as io
from abkhazia.kaldi.kaldi_path import kaldi_path
import abkhazia.kaldi.abstract_recipe as abstract_recipe


class LanguageModel(abstract_recipe.AbstractRecipe):
    """Compute a language model from an abkhazia corpus"""

    name = 'language'

    def __init__(self, corpus_dir, recipe_dir=None, verbose=False, njobs=1):
        super(LanguageModel, self).__init__(corpus_dir, recipe_dir, verbose)
        self.lang_dir = os.path.join(self.recipe_dir, 'lang')

        self.njobs = njobs
        self.level = 'phone'
        self.order = 3
        self.silence_probability = 0.5  # default from kaldi prepare_lang.sh
        self.position_dependent_phones = True
        # here we could use a different silence_prob. I think however that
        # --position-dependent-phones has to be the same as what was used for
        # training (as well as the phones.txt, extra_questions.txt and
        # nonsilence_phones.txt), otherwise the mapping between phones and
        # acoustic state in the trained model will be lost

    def _check_level(self):
        level_choices = ['word', 'phone']
        if self.level not in level_choices:
            raise RuntimeError(
                'language model level must be in {}, it is {}'
                .format(level_choices, self.level))

    def _check_order(self):
        if not isinstance(self.order, int) or self.order < 1:
            raise RuntimeError(
                'language model order must be interger > 0, it is {}'
                .format(self.order))

    def _check_silence_probability(self):
        if self.silence_probability > 1 or self.silence_probability < 0:
            raise RuntimeError(
                'silence probability must be in [0, 1], it is {}'
                .format(self.silence_probability))

    def check_parameters(self):
        self._check_level()
        self._check_order()
        self._check_silence_probability()

    def _prepare_lang(self):
        # First need to do a prepare_lang in the desired folder to get
        # to use the right "phone" or "word" lexicon irrespective of
        # what was used as a lexicon in training. If
        # word_position_dependent is true and the lm is at the phone
        # level, use prepare_lang_wpdpl.sh in the local folder,
        # otherwise we fall back to the original utils/prepare_lang.sh
        # (some slight customizations of the script are necessary to
        # decode with a phone loop language model when word position
        # dependent phone variants have been trained).
        script_prepare_lm = os.path.join(
            self.recipe_dir, 'utils/prepare_lang.sh')

        share_dir = pkg_resources.resource_filename(
            pkg_resources.Requirement.parse('abkhazia'), 'abkhazia/share')
        script_prepare_lm_wpdpl = os.path.join(
            share_dir, 'prepare_lang_wpdpl.sh')

        script = (script_prepare_lm_wpdpl
                  if self.level == 'phone' and self.position_dependent_phones
                  else script_prepare_lm)

        command = (
            script +
            ' --position-dependent-phones {0}'
            ' --sil_prob {1} {2} "<unk>" {3} {4}'.format(
                'true' if self.position_dependent_phones else 'false',
                self.silence_probability,
                os.path.join(self.a2k._local_path()),
                os.path.join(self.lang_dir, 'local'),
                self.lang_dir))

        self.log.info('running %s', os.path.basename(script))
        utils.jobs.run(
            command, stdout=self.log.debug,
            cwd=self.recipe_dir, env=kaldi_path())

    def create(self):
        """Create the recipe data in `self.recipe_dir`"""
        # check we have either word or phone level
        self._check_level()

        # setup data files common to both levels
        self.a2k.setup_phones()
        self.a2k.setup_silences()
        self.a2k.setup_variants()

        desired_utts = self.a2k.desired_utterances(njobs=self.njobs)
        text = self.a2k.setup_text(desired_utts=desired_utts)

        # setup lm lexicon and input text depending on model level
        lm_text = os.path.join(self.a2k._local_path(), 'lm_text.txt')
        lexicon = self.a2k.setup_lexicon()
        if self.level == 'word':
            shutil.copy(text, lm_text)
        else:  # phone level
            io.word2phone(lexicon, text, lm_text)
            self.a2k.setup_phone_lexicon()

        self.a2k.setup_kaldi_folders()
        self.a2k.setup_machine_specific_scripts()
        self.a2k.setup_prepare_lang_wpdpl()

    def _compile_fst(self, G_txt, G_fst):
        """Compile and sort a text FST to kaldi binary FST"""
        self._log.info('compiling %s to %s', G_txt, G_fst)
        temp = tempfile.NamedTemporaryFile('w', delete=False)

        # txt to temp
        command1 = (
            ' fstcompile --isymbols={0} --osymbols={0}'
            ' --keep_isymbols=false --keep_osymbols=false {1}'
            .format(os.path.join(self._output_dir, 'words.txt'), G_txt))
        self._log.debug('running %s > %s', command1, temp)
        utils.jobs.run(command1, temp.write)

        # temp to fst
        command2 = (
            'fstarcsort --sort_type=ilabel {}'.format(temp.name))
        self._log.debug('running %s > %s', command2, G_fst)
        utils.jobs.run(command2, open(G_fst, 'w').write)

        utils.remove(temp.name)

    def _compute_lm(self, G_arpa):
        self.log.info('creating %s', G_arpa)
        # generate ARPA/MIT n-gram with IRSTLM Train need to remove
        # utt-id on first column of text file TODO and test? ->
        # compare the diff with/without
        lm_text = os.path.join(self.a2k._local_path(), 'lm_text.txt')
        text_ready = os.path.join(self.a2k._local_path(), 'text_ready.txt')
        text_se = os.path.join(self.a2k._local_path(), 'text_se.txt')
        text_lm = os.path.join(self.a2k._local_path(), 'text_lm.gz')
        text_blm = os.path.join(self.a2k._local_path(), 'text_blm.gz')

        try:
            # cut -d' ' -f2 < lm_text > text_ready
            with open(text_ready, 'w') as ready:
                ready.write('\n'.join(
                    [' '.join(line.split()[1:])
                     for line in open(lm_text, 'r').xreadlines()]))

            utils.jobs.run(
                'add-start-end.sh',
                stdin=open(text_ready, 'r'),
                stdout=open(text_se, 'w').write,
                env=kaldi_path(), cwd=self.recipe_dir)

            # k option is number of split, useful for huge text files
            # build-lm.sh in kaldi/tools/irstlm/bin
            command = ('build-lm.sh -i {0} -n {1} -o {2} -k 1 -s kneser-ney'
                       .format(text_se, self.order, text_lm))
            utils.jobs.run(
                command,
                stdout=self.log.debug,
                env=kaldi_path(), cwd=self.recipe_dir)

            command = ('compile-lm -i {} --text=yes {}'
                       .format(text_lm, text_blm))
            utils.jobs.run(
                command,
                stdout=self.log.debug,
                env=kaldi_path(), cwd=self.recipe_dir)

            # gzip the compiled lm (from
            # https://docs.python.org/2/library/gzip.html#examples-of-usage)
            with open(text_blm, 'rb') as fin, gzip.open(G_arpa, 'wb') as fout:
                shutil.copyfileobj(fin, fout)

        finally:  # remove temp files
            for f in (text_ready, text_se, text_lm, text_blm):
                utils.remove(f)

    def _format_lm(self, G_arpa, G_fst):
        """generate FST (use the SRILM library)"""
        # Includes adapting the vocabulary to lexicon in out_dir
        # srilm_opts: do not use -tolower by default, since we do not
        # make assumption that lexicon has no meaningful
        # lowercase/uppercase distinctions (and if in unicode, no idea
        # what lowercasing would produce)
        self.log.info('creating language model in %s', G_fst)

        # format_lm_sri.sh copies stuff so we need to instantiate
        # another folder and then clean up (or we could do a custom
        # format_lm_sri.sh with $1 and $4 == $1 and no cp)
        tmp_dir = tempfile.mkdtemp()

        try:
            command = ('utils/format_lm_sri.sh '
                       '--srilm_opts "-subset -prune-lowprobs -unk" '
                       '{0} {1} {2}'.format(
                           self.lang_dir, G_arpa, tmp_dir))
            utils.jobs.run(
                command,
                stdout=self.log.debug,
                env=kaldi_path(), cwd=self.recipe_dir)

            utils.remove(self.lang_dir)
            shutil.move(tmp_dir, self.lang_dir)
        finally:
            try:
                utils.remove(tmp_dir)
            except:
                pass

    def run(self):
        self.check_parameters()
        self._prepare_lang()

        # - G.arpa.gz MIT/ARPA formatted n-gram is already
        #   provided in input_dir
        # - A text.txt file from which to estimate a n-gram is
        #   provided in input_dir
        local = self.a2k._local_path()
        G_txt = os.path.join(local, 'G.txt')
        G_fst = os.path.join(local, 'G.fst')
        G_arpa = os.path.join(local, 'G.arpa.gz')

        # G.txt file is already provided (FST grammar in text format)
        if os.path.isfile(G_txt):
            self._compile_fst(G_txt, G_fst)
        else:
            if not os.path.isfile(G_arpa):
                self._compute_lm(G_arpa)
            self._format_lm(G_arpa, G_fst)

    def export(self):
        """Export data/dict/G.fst in export/language_model.fst"""
        origin = os.path.join(self.recipe_dir, self.lang_dir, 'G.fst')
        target = os.path.join(self.recipe_dir, 'export', 'language_model.fst')
        self.log.info('writing %s', target)

        dirname = os.path.dirname(target)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        shutil.copy(origin, target)
