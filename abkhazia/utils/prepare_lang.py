# Copyright 2017 Thomas Schatz, Xuan-Nga Cao, Mathieu Bernard
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
"""Wrapper on the Kaldi wsj/utils/prepare_lang.sh script"""

import os

from abkhazia.utils import logger, jobs, bool2str, remove
from abkhazia.kaldi import kaldi_path, Abkhazia2Kaldi


def prepare_lang(
        corpus,
        output_dir,
        level='word',
        silence_probability=0.5,
        position_dependent_phones=False,
        keep_tmp_dirs=False,
        log=logger.null_logger()):
    """Wrapper on the Kaldi wsj/utils/prepare_lang.sh script

    Create the directory `output_dir` and populate it as described in
    http://kaldi-asr.org/doc/data_prep.html#data_prep_lang_creating. It
    produces (among other files) the L.fst part of the HCLG model.

    Parameters:
    -----------

    corpus (Corpus): abkhazia corpus to prepare lang for.

    output_dir (path): directory where to write prepared files,
      created if nonexisting.

    level ('word' or 'phone'): set to 'word' (the default) to prepare
      the corpus at word level, or 'phone' to prepare it at phone
      level. The prepared data will be used to train language and
      acoustic models at either word or phone level.

    silence_probability (float): The probability to have a silence
      phone. Usually 0.0 or 0.5, default is 0.5.

    position_dependent_phones (bool): default to False. Should be set
      to true or false depending on whether the language model
      produced is destined to be used with an acoustic model trained
      with or without word position dependent variants of the phones.

    keep_tmp_dir (bool): default to False. If true, keep the
      directories 'recipe' and 'local' in `output_dir`, if false
      remove them before returning.

    log (logger.Logging): the logger instance where to send messages,
      default is too disable the log.

    Return:
    -------

    The return code of the Kaldi prepare_lang script. 0 for success,
    any other for error.

    """
    output_dir = os.path.abspath(output_dir)
    log.info('preparing lexicon in %s (L.fst)...', output_dir)

    # init the kaldi recipe in output_dir/recipe
    a2k = Abkhazia2Kaldi(
        corpus, os.path.join(output_dir, 'recipe'), name='dict', log=log)

    a2k.setup_phones()
    a2k.setup_silences()
    a2k.setup_variants()
    a2k.setup_kaldi_folders()
    a2k.setup_machine_specific_scripts()

    if level == 'word':
        a2k.setup_lexicon()
    else:
        a2k.setup_phone_lexicon()

    # choosing the script according to level and word position
    # dependent phones. If word_position_dependent is true and the lm
    # is at the phone level, use prepare_lang_wpdpl.sh in the local
    # folder, otherwise we fall back to the original prepare_lang.sh
    # (some slight customizations of the script are necessary to
    # decode with a phone loop language model when word position
    # dependent phone variants have been trained).
    script_prepare_lm = os.path.join(
        a2k.kaldi_root, 'egs', 'wsj', 's5', 'utils', 'prepare_lang.sh')

    script_prepare_lm_wpdpl = os.path.join(
        a2k.share_dir, 'prepare_lang_wpdpl.sh')

    script = (script_prepare_lm_wpdpl
              if level == 'phone' and position_dependent_phones
              else script_prepare_lm)

    # generate the bash command we will run
    command = (
        script + ' --position-dependent-phones {wpd}'
        ' --sil-prob {sil} {input} "<unk>" {temp} {output}'.format(
            wpd=bool2str(position_dependent_phones),
            sil=silence_probability,
            input=os.path.join(a2k._local_path()),
            temp=os.path.join(output_dir, 'local'),
            output=output_dir))

    # run the command in Kaldi and forward its return code
    log.info('running "%s"', command)
    try:
        return jobs.run(
            command, cwd=a2k.recipe_dir, env=kaldi_path(), stdout=log.debug)
    finally:
        if not keep_tmp_dirs:
            remove(a2k.recipe_dir)
            remove(os.path.join(output_dir, 'local'))
