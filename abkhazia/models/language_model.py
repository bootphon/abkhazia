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
import re
import shutil
import tempfile

import abkhazia.utils as utils
import abkhazia.models.abstract_recipe as abstract_recipe
from abkhazia.kaldi import kaldi_path


def check_language_model(lm_dir):
    """Raise IOError if oov.int, G.fst and G.arpa.fst are not in `lm_dir`"""
    utils.check_directory(
        lm_dir,
        ['oov.int', 'G.fst', 'G.arpa.gz', 'phones.txt'],
        name='language model')


def read_params(lm_dir):
    """Parse the file `lm_dir`/params.txt and return a pair (lm_level, lm_order)

    Raises IOError on error

    """
    params = os.path.join(lm_dir, 'params.txt')
    if not os.path.isfile(params):
        raise IOError('{} file not found'.format(params))

    return open(params, 'r').readline().strip().split(' ')


def read_int2phone(lm_dir, word_position_dependent=True):
    """Return a int to phone mapping as a dict

    Kaldi internally codes phones as ints, so this method reverses the
    mapping from ints to phones based on the phones.txt file in
    `lm_dir`. This file is assumed to exist.

    """
    phonemap = dict()
    for line in utils.open_utf8(os.path.join(lm_dir, 'phones.txt'), 'r'):
        phone, code = line.strip().split(' ')

        # remove word position markers
        if word_position_dependent and phone[-2:] in ['_I', '_B', '_E', '_S']:
            phone = phone[:-2]

        phonemap[code] = phone
    return phonemap


class LanguageModel(abstract_recipe.AbstractRecipe):
    """Compute a language model from an abkhazia corpus

    This class uses Kaldi, IRSTLM and SRILM to compute n-grams
    language models from any abkhazia speech corpus. The models can be
    either at word or phone level.

    Example:

    The following exemple compute a word level trigram without
    optional silences::

        corpus = Corpus.load('/path/to/corpus')
        lm = LanguageModel(corpus)
        lm.order = 3
        lm.level = 'word'
        lm.silence_probability = 0.0
        lm.create()
        lm.run()

    Attributes:
        level (str): 'phone' or 'word' language model
        order (int): order of the language model (n in n-gram)
        silence_probability (float)
        position_dependent_phone (bool)

    """

    name = 'language'

    def __init__(self, corpus, output_dir, log=utils.null_logger()):
        super(LanguageModel, self).__init__(corpus, output_dir, log=log)

        # setup default values for parameters from the configuration
        # file. Here we could use a different
        # silence_probability. Thomas thinks however that
        # position_dependent_phones has to be the same as what was
        # used for training (as well as the phones.txt,
        # extra_questions.txt and nonsilence_phones.txt), otherwise
        # the mapping between phones and acoustic state in the trained
        # model will be lost.
        def config(name):
            """Quick access to LM configuration"""
            return utils.config.get('language', name)
        self.level = config('model-level')
        self.order = config('model-order')

        # 0.5 is the default from kaldi wsj/utils/prepare_lang.sh
        self.silence_probability = (
            0.5 if config('optional-silence') is 'true' else 0.0)
        self.position_dependent_phones = config('word-position-dependent')

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
        if self.silence_probability >= 1 or self.silence_probability < 0:
            raise RuntimeError(
                'silence probability must be in [0, 1], it is {}'
                .format(self.silence_probability))

    def _check_position_dependent(self):
        # if bool, convert to str
        self.position_dependent_phones = utils.bool2str(
            self.position_dependent_phones)

    def _setup_prepare_lang_wpdpl(self):
        """Prepare language/lang/ folder for word position dependent models"""
        local = os.path.join(self.recipe_dir, 'local')
        if not os.path.isdir(local):
            os.makedirs(local)

        share = pkg_resources.resource_filename(
            pkg_resources.Requirement.parse('abkhazia'), 'abkhazia/share')

        for target in ('prepare_lang_wpdpl.sh', 'validate_lang_wpdpl.pl'):
            shutil.copy(
                os.path.join(share, target),
                os.path.join(local, target))

    def _prepare_lang(self):
        """Prepare the corpus data for language modeling"""
        # First need to do a prepare_lang in the desired folder to get
        # to use the right "phone" or "word" lexicon irrespective of
        # what was used as a lexicon in training. If
        # word_position_dependent is true and the lm is at the phone
        # level, use prepare_lang_wpdpl.sh in the local folder,
        # otherwise we fall back to the original utils/prepare_lang.sh
        # (some slight customizations of the script are necessary to
        # decode with a phone loop language model when word position
        # dependent phone variants have been trained).
        self.log.info('preprocessing corpus')

        script_prepare_lm = os.path.join(
            self.recipe_dir, 'utils/prepare_lang.sh')

        share_dir = pkg_resources.resource_filename(
            pkg_resources.Requirement.parse('abkhazia'), 'abkhazia/share')
        script_prepare_lm_wpdpl = os.path.join(
            share_dir, 'prepare_lang_wpdpl.sh')

        script = (script_prepare_lm_wpdpl
                  if self.level == 'phone' and
                  utils.str2bool(self.position_dependent_phones) is True
                  else script_prepare_lm)

        self._run_command(
            script + ' --position-dependent-phones {0}'
            ' --sil-prob {1} {2} "<unk>" {3} {4}'.format(
                self.position_dependent_phones,
                self.silence_probability,
                os.path.join(self.a2k._local_path()),
                os.path.join(self.output_dir, 'local'),
                self.output_dir))

    def _compile_fst(self, G_txt, G_fst):
        """Compile and sort a text FST to kaldi binary FST

        This method relies on the Kaldi programs fstcompile and
        fstarcsort.

        """
        self.log.info('compiling text FST to binary FST')

        temp = tempfile.NamedTemporaryFile('w', delete=False)
        try:
            # txt to temp
            command1 = (
                'fstcompile --isymbols={0} --osymbols={0}'
                ' --keep_isymbols=false --keep_osymbols=false {1}'
                .format(os.path.join(self.output_dir, 'words.txt'), G_txt))
            self.log.debug('running %s > %s', command1, temp)
            utils.jobs.run(command1, temp.write)

            # temp to fst
            command2 = (
                'fstarcsort --sort_type=ilabel {}'.format(temp.name))
            self.log.debug('running %s > %s', command2, G_fst)
            utils.jobs.run(command2, open(G_fst, 'w').write)

        finally:
            utils.remove(temp.name, safe=True)

    def _compute_lm(self, G_arpa):
        """Generate an ARPA n-gram from an abkhazia corpus

        This method relies on the following Kaldi programs:
        add-start-end.sh, build-lm.sh and compile-lm. It uses the
        IRSTLM library.

        """
        self.log.info(
            'computing %s %s-gram in ARPA format', self.level, self.order)

        # cut -d' ' -f2 lm_text > text_ready. Train need to
        # remove utt-id on first column of text file
        lm_text = os.path.join(self.a2k._local_path(), 'lm_text.txt')
        text_ready = os.path.join(self.a2k._local_path(), 'text_ready.txt')
        with utils.open_utf8(text_ready, 'w') as ready:
            ready.write('\n'.join(
                [' '.join(line.split()[1:])
                 for line in utils.open_utf8(lm_text, 'r').xreadlines()]))

        text_se = os.path.join(self.a2k._local_path(), 'text_se.txt')
        utils.jobs.run(
            'add-start-end.sh',
            stdin=open(text_ready, 'r'),
            stdout=open(text_se, 'w').write,
            env=kaldi_path(), cwd=self.recipe_dir)
        assert os.path.isfile(text_se), 'LM failed on add-start-end'

        # k option is number of split, useful for huge text files
        # build-lm.sh in kaldi/tools/irstlm/bin
        text_lm = os.path.join(self.a2k._local_path(), 'text_lm.gz')
        self._run_command(
            'build-lm.sh -i {0} -n {1} -o {2} -k 1 -s kneser-ney'
            .format(text_se, self.order, text_lm))
        assert os.path.isfile(text_lm), 'LM failed on build-lm'

        text_blm = os.path.join(self.a2k._local_path(), 'text_blm.gz')
        self._run_command(
            # was with the -i option
            'compile-lm {} --text=yes {}'.format(text_lm, text_blm))

        # gzip the compiled lm (from
        # https://docs.python.org/2/library/gzip.html#examples-of-usage)
        with open(text_blm, 'rb') as fin, gzip.open(G_arpa, 'wb') as fout:
            shutil.copyfileobj(fin, fout)

    # def _format_lm(self, G_arpa, G_fst):
    #     """Generate FST from ARPA language model

    #     This methods relies on Kaldi `utils/format_lm_sri.sh`, which
    #     use the SRILM library. It includes adapting the vocabulary to
    #     the corpus lexicon.

    #     May issue a warning 'gzip: stdout: Broken pipe' but this does
    #     not corrupt the computation.

    #     May issue warnings such as '-: line 340912: warning: 13585
    #     1-grams read, expected 13590', this is the effect of OOV
    #     pruning in kaldi tools/srilm/bin/change-lm-vocab, so not a
    #     problem nor a bug (the doesn't update ngrams count after
    #     pruning).

    #     """
    #     self.log.info('converting ARPA to FST')

    #     # format_lm_sri.sh copies stuff so we need to instantiate
    #     # another folder and then clean up (or we could do a custom
    #     # format_lm_sri.sh with $1 and $4 == $1 and no cp)
    #     tmp_dir = tempfile.mkdtemp()
    #     try:
    #         # srilm_opts: do not use -tolower by default, since we do not
    #         # make assumption that lexicon has no meaningful
    #         # lowercase/uppercase distinctions (and if in unicode, no idea
    #         # what lowercasing would produce)
    #         self._run_command(
    #             'utils/format_lm_sri.sh '
    #             '--srilm_opts "-subset -prune-lowprobs -unk" {0} {1} {2}'
    #             .format(self.output_dir, G_arpa, tmp_dir))
    #         utils.remove(self.output_dir)
    #         shutil.move(tmp_dir, self.output_dir)
    #     finally:
    #         utils.remove(tmp_dir, safe=True)

    #         # In this kaldi script, gzip fails with the message "gzip:
    #         # stdout: Broken pipe". This leads the logfile to be
    #         # closed, so we reopen it here. Actually we loose the log
    #         # messages from arpa2fst and fstisstochastic. But thoses
    #         # message are still readable on stdout with --verbose
    #         utils.log2file.reopen_files(self.log)

    def _change_lm_vocab(self, lm_txt, words_txt):
        """Create a LM from an existing one by changing its vocabulary

        All n-grams in the new vocab are retained with their original
        probabilities. Backoff weights are recomputed and backed-off
        unigrams for all new words are added. -subset option performs
        subsetting of the vocabulary without adding new words.

        This is reimplementation of the change-lm-vocab script from
        SRILM, modified in 3 ways:

         - no more -tolower option

         - the pruning step now updates ngrams count in the header
           (disable annoying warning)

         - the call to ngram is done in 2 steps if the 1 step failed
           (-renorm and prune-lowprobs options failed together on
           -librispeech-test-clean, need 2 calls)

        """
        out_lm = os.path.join(self.output_dir, 'out_lm.txt')
        self.log.debug('pruning vocabulary in %s', out_lm)

        words = set(w.split()[0] for w in utils.open_utf8(words_txt, 'r'))
        lm = utils.arpa.ARPALanguageModel.load(lm_txt)
        lm.prune_vocabulary(words)
        lm_pruned = lm_txt + '.pruned'
        lm.save(lm_pruned)

        try:
            self._run_command(
                'ngram -lm {0} -vocab /dev/null -renorm -write-lm {1} '
                '-prune-lowprobs -unk -order {2}'
                .format(lm_pruned, out_lm, self.order))
        except RuntimeError:
            self._run_command(
                'utils/run.pl {3} '
                'ngram -lm {0} -vocab /dev/null -write-lm - '
                '-prune-lowprobs -unk -order {2} | '
                'ngram -lm - -vocab /dev/null -renorm -unk '
                '-order {2} -write-lm {1}'
                .format(lm_pruned, out_lm, self.order,
                        os.path.join(self.output_dir, 'ngram.log')))

        return out_lm

    def _format_lm(self, arpa_lm, fst_lm):
        """Converts ARPA-format language models to FSTs

        Change the LM vocabulary using SRILM. This is a Python
        implementation of Kaldi egs/wsj/s5/utils/format_lm_sri.sh,
        with margin modifications.

        Note: if you want to just convert ARPA LMs to FSTs, there is a
        simpler way to do this that doesn't require SRILM: see
        examples in Kaldi egs/wsj/s5/local/wsj_format_local_lms.sh

        """
        self.log.info('converting ARPA to FST')

        words_txt = os.path.join(self.output_dir, 'words.txt')
        for _file in (arpa_lm, words_txt):
            if not os.path.isfile(_file):
                raise IOError('excpected input file {} to exist'.format(_file))

        lm_base = os.path.splitext(os.path.basename(arpa_lm))[0]
        tempdir = self.output_dir  # tempfile.mkdtemp()
        try:
            # unzip the input LM. Removing all "illegal" combinations of
            # <s> and </s>, which are supposed to occur only at being/end
            # of utt. These can cause determinization failures of CLG
            # [ends up being epsilon cycles].
            lm_txt = os.path.join(tempdir, lm_base + '.txt')
            # self.log.debug('unzip %s to %s', arpa_lm, lm_txt)
            with utils.open_utf8(lm_txt, 'w') as fp:
                for line in gzip.open(arpa_lm, 'rb'):
                    if not (re.search('<s> <s>', line) or
                            re.search('</s> <s>', line) or
                            re.search('</s> </s>', line)):
                        fp.write(line)

            # finds words in the arpa LM that are not symbols in the
            # OpenFst-format symbol table words.txt
            oovs = os.path.join(self.output_dir, 'oovs_{}.txt'.format(lm_base))
            self.log.debug('write OOVs to %s', oovs)
            utils.jobs.run(
                'utils/find_arpa_oovs.pl {} {}'.format(words_txt, lm_txt),
                stdout=utils.open_utf8(oovs, 'w').write,
                env=kaldi_path(),
                cwd=self.recipe_dir)

            # Change the LM vocabulary to be the intersection of the
            # current LM vocabulary and the set of words in the
            # pronunciation lexicon. This also renormalizes the LM by
            # recomputing the backoff weights, and remove those ngrams
            # whose probabilities are lower than the backed-off
            # estimates.
            lm_pruned = self._change_lm_vocab(lm_txt, words_txt)

            # convert from ARPA to FST
            self._run_command(
                'utils/run.pl {0} arpa2fst {1} | fstprint | '
                'utils/eps2disambig.pl | utils/s2eps.pl | '
                'fstcompile --isymbols={2} --osymbols={2} '
                '--keep_isymbols=false --keep_osymbols=false | '
                'fstrmepsilon | fstarcsort --sort_type=ilabel > {3}'.format(
                    os.path.join(self.output_dir, 'format_lm.log'),
                    lm_pruned, words_txt, fst_lm))

            # The output is like: 9.14233e-05 -0.259833. We do expect
            # the first of these 2 numbers to be close to zero (the
            # second is nonzero because the backoff weights make the
            # states sum to >1).
            try:
                self._run_command('fstisstochastic {}'.format(fst_lm))
            except RuntimeError:
                pass

        finally:
            pass  # utils.remove(tempdir)

    def check_parameters(self):
        """Raise if the language modeling parameters are not correct"""
        super(LanguageModel, self).check_parameters()
        self._check_level()
        self._check_order()
        self._check_silence_probability()
        self._check_position_dependent()

    def create(self):
        """Initialize the recipe data in `self.recipe_dir`"""
        self.check_parameters()

        # setup phones
        self.a2k.setup_phones()
        self.a2k.setup_silences()
        self.a2k.setup_variants()

        # setup lexicon and text depending on word/phone ngram level
        text = self.a2k.setup_text()
        lm_text = os.path.join(self.a2k._local_path(), 'lm_text.txt')
        if self.level == 'word':
            shutil.copy(text, lm_text)
            self.a2k.setup_lexicon()
        else:  # phone level
            with utils.open_utf8(lm_text, 'w') as out:
                for k, v in sorted(self.corpus.phonemize_text().iteritems()):
                    out.write(u'{} {}\n'.format(k, v))
            self.a2k.setup_phone_lexicon()

        # setup data files common to both levels
        self.a2k.setup_kaldi_folders()
        self.a2k.setup_machine_specific_scripts()
        self._setup_prepare_lang_wpdpl()

    def run(self):
        """Run the created recipe and compute the language model"""
        self._prepare_lang()

        def _local(f):
            return os.path.join(self.a2k._local_path(), f)
        g_txt = _local('G.txt')
        g_fst = _local('G.fst')
        g_arpa = _local('G.arpa.gz')

        # G.txt file is already provided (FST grammar in text format)
        if os.path.isfile(g_txt):
            self._compile_fst(g_txt, g_fst)
        else:
            # G.arpa.gz MIT/ARPA formatted n-gram is not already
            # provided in input_dir: compute it from corpus text
            if not os.path.isfile(g_arpa):
                self._compute_lm(g_arpa)
            self._format_lm(g_arpa, g_fst)

    def export(self):
        super(LanguageModel, self).export()

        # G.arpa.gz is needed for acoustic modeling
        for g in ('G.arpa.gz', 'G.fst'):
            origin = os.path.join(
                self.recipe_dir, 'data', 'local', self.name, g)
            target = os.path.join(self.output_dir, g)
            shutil.copy(origin, target)

        # write a little file with LM parameters
        with open(os.path.join(self.output_dir, 'params.txt'), 'w') as param:
            param.write('{} {}\n'.format(self.level, self.order))
