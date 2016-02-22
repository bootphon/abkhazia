# Copyright 2015, 2016 Thomas Schatz, Xuan Nga Cao, Mathieu Bernard
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

import codecs
import os
import shutil
import subprocess

import abkhazia.utils.basic_io as io


def get_dict_path(recipe_path, name='dict'):
    """Return `recipe_path`/data/local/`name`

    Create the directory if it does not exist

    """
    dict_path = os.path.join(recipe_path, 'data', 'local', name)
    if not os.path.isdir(dict_path):
        os.makedirs(dict_path)
    return dict_path


def setup_lexicon(corpus_path, recipe_path,
                  prune_lexicon=False, train_name=None,
                  name='dict'):
    dict_path = get_dict_path(recipe_path, name)
    if prune_lexicon:
        # get words appearing in train part
        train_text = os.path.join(
            corpus_path, 'data', 'split', train_name, 'text.txt')

        _, utt_words = io.read_text(train_text)
        allowed_words = set([word for utt in utt_words for word in utt])

        # add special OOV word <unk>
        allowed_words.add(u'<unk>')

        # remove other words from the lexicon
        allowed_words = list(allowed_words)
        io.copy_first_col_matches(
            os.path.join(corpus_path, 'data', 'lexicon.txt'),
            os.path.join(dict_path, 'lexicon.txt'),
            allowed_words)
    else:
        shutil.copy(os.path.join(corpus_path, 'data', 'lexicon.txt'),
                    os.path.join(dict_path, 'lexicon.txt'))


def setup_phone_lexicon(corpus_path, recipe_path, name):
    dict_path = get_dict_path(recipe_path, name)
    # get list of phones (including silence and non-silence phones)
    with codecs.open(os.path.join(dict_path, 'nonsilence_phones.txt'),\
                     mode='r', encoding="UTF-8") as inp:
        lines = inp.readlines()
    phones = [line.strip() for line in lines]
    with codecs.open(os.path.join(dict_path, 'silence_phones.txt'),\
                     mode='r', encoding="UTF-8") as inp:
        lines = inp.readlines()
    phones = phones + [line.strip() for line in lines]
    # create 'phone' lexicon
    with codecs.open(os.path.join(dict_path, 'lexicon.txt'),\
                     mode='w', encoding="UTF-8") as out:
        for word in phones:
            out.write(u'{0} {1}\n'.format(word, word))
        # add <unk> word, in case one wants to use the phone loop
        # lexicon for training it also is necessary if one doesn't
        # want to modify the validating scripts too much
        out.write(u'<unk> SPN\n')


def setup_phones(corpus_path, recipe_path, name='dict'):
    dict_path = get_dict_path(recipe_path, name)
    with codecs.open(os.path.join(corpus_path, 'data', 'phones.txt'),
                     mode='r', encoding='UTF-8') as inp:
        lines = inp.readlines()
    with codecs.open(os.path.join(dict_path, 'nonsilence_phones.txt'),
                     mode='w', encoding='UTF-8') as out:
        for line in lines:
            symbol = line.split(u' ')[0]
            out.write(u"{0}\n".format(symbol))


def setup_silences(corpus_path, recipe_path, name='dict'):
    dict_path = get_dict_path(recipe_path, name)
    shutil.copy(os.path.join(corpus_path, 'data', 'silences.txt'),
                os.path.join(dict_path, 'silence_phones.txt'))
    with codecs.open(os.path.join(dict_path, 'optional_silence.txt'),
                     mode='w', encoding='UTF-8') as out:
        out.write(u'SIL\n')


def setup_variants(corpus_path, recipe_path, name='dict'):
    dict_path = get_dict_path(recipe_path, name)
    shutil.copy(os.path.join(corpus_path, 'data', 'variants.txt'),
                os.path.join(dict_path, 'extra_questions.txt'))


def get_data_path(corpus_path, recipe_path, in_split=None, out_split=None):
    if in_split is None:
        inp = os.path.join(corpus_path, 'data')
    else:
        inp = os.path.join(corpus_path, 'data', 'split', in_split)
    assert os.path.isdir(inp), "Directory doesn't exist: {0}".format(inp)
    if out_split is None:
        out = os.path.join(recipe_path, 'data', 'main')
    else:
        out = os.path.join(recipe_path, 'data', out_split)
    if not(os.path.isdir(out)):
        os.makedirs(out)
    return inp, out


def setup_text(corpus_path, recipe_path,
               in_split=None, out_split=None, desired_utts=None):
    i_path, o_path = get_data_path(
        corpus_path, recipe_path, in_split, out_split)

    if desired_utts is None:
        shutil.copy(os.path.join(i_path, 'text.txt'),
                    os.path.join(o_path, 'text'))
    else:
        io.copy_first_col_matches(
                os.path.join(i_path, 'text.txt'),
                os.path.join(o_path, 'text'),
                desired_utts)


def setup_phone_text(corpus_path, recipe_path, in_split=None, out_split=None, desired_utts=None):
    i_path, o_path = get_data_path(corpus_path, recipe_path, in_split, out_split)
    if desired_utts is None:
        shutil.copy(os.path.join(i_path, 'text.txt'), p.join(o_path, 'text'))
    else:
        io.copy_first_col_matches(os.path.join(i_path, 'text.txt'),
                                    os.path.join(o_path, 'text'),
                                    desired_utts)


def setup_utt2spk(corpus_path, recipe_path, in_split=None, out_split=None, desired_utts=None):
    i_path, o_path = get_data_path(corpus_path, recipe_path, in_split, out_split)
    if desired_utts is None:
        shutil.copy(os.path.join(i_path, 'utt2spk.txt'), os.path.join(o_path, 'utt2spk'))
    else:
        io.copy_first_col_matches(os.path.join(i_path, 'utt2spk.txt'),
                                  os.path.join(o_path, 'utt2spk'),
                                    desired_utts)


def setup_segments(corpus_path, recipe_path, in_split=None, out_split=None, desired_utts=None):
    i_path, o_path = get_data_path(corpus_path, recipe_path, in_split, out_split)
    with codecs.open(os.path.join(i_path, 'segments.txt'),
                     mode='r', encoding='UTF-8') as inp:
        lines = inp.readlines()
    # write only if starts and stops are specified in segments.txt
    if len(lines[0].strip().split(u" ")) == 4:
        if not(desired_utts is None):
            # select utterances that are long enough (>= 15 ms)
            lines = io.match_on_first_col(lines, desired_utts)
        with codecs.open(os.path.join(o_path, 'segments'),
                         mode='w', encoding='UTF-8') as out:
            for line in lines:
                elements = line.strip().split(u" ")
                utt_id, wav_id = elements[:2]
                record_id = os.path.splitext(wav_id)[0]
                out.write(u" ".join([utt_id, record_id] + elements[2:]) + u"\n")


def setup_wav(corpus_path, recipe_path,
              in_split=None, out_split=None, desired_utts=None):
    i_path, o_path = get_data_path(
        corpus_path, recipe_path, in_split, out_split)

    # get list of wavs from segments.txt
    with codecs.open(os.path.join(i_path, 'segments.txt'),
                     mode='r', encoding='UTF-8') as inp:
        lines = inp.readlines()

    if desired_utts is not None:
        # select utterances that are long enough (>= 15 ms)
        lines = io.match_on_first_col(lines, desired_utts)
    wavs = set()
    for line in lines:
        elements = line.strip().split(u" ")
        wav_id = elements[1]
        wavs.add(wav_id)
    # write wav.scp
    with codecs.open(os.path.join(o_path, 'wav.scp'),
                     mode='w', encoding='UTF-8') as out:
        for wav_id in wavs:
            record_id = os.path.splitext(wav_id)[0]
            wav_full_path = os.path.join(os.path.abspath(recipe_path), 'wavs', wav_id)
            out.write(u"{0} {1}\n".format(record_id, wav_full_path))


def setup_wav_folder(corpus_path, recipe_path):
    # using a symbolic link to avoid copying
    # voluminous data
    link_name = os.path.join(recipe_path, 'wavs')
    target = os.path.join(corpus_path, 'data', 'wavs')
    if os.path.exists(link_name):
        # could log this...
        os.remove(link_name)
    os.symlink(target, link_name)


def setup_kaldi_folders(kaldi_root, recipe_path):
    steps_dir = os.path.abspath(os.path.join(kaldi_root, 'egs', 'wsj', 's5', 'steps'))
    steps_link = os.path.abspath(os.path.join(recipe_path, 'steps'))
    if os.path.exists(steps_link):
        os.remove(steps_link)
    utils_dir = os.path.abspath(os.path.join(kaldi_root, 'egs', 'wsj', 's5', 'utils'))
    utils_link = os.path.abspath(os.path.join(recipe_path, 'utils'))
    if os.path.exists(utils_link):
        os.remove(utils_link)
    subprocess.call("ln -s {0} {1}".format(steps_dir, steps_link), shell=True)
    subprocess.call("ln -s {0} {1}".format(utils_dir, utils_link), shell=True)
    conf_dir = os.path.join(recipe_path, 'conf')
    if os.path.exists(conf_dir):
        shutil.rmtree(conf_dir)
    os.mkdir(conf_dir)
    # create mfcc.conf file (following what seems to be commonly used in other kaldi recipes)
    with open(os.path.join(conf_dir, 'mfcc.conf'), mode='w') as out:
        out.write("--use-energy=false   # only non-default option.\n")
    # create empty pitch.conf file (required when using mfcc + pitch features)
    with open(os.path.join(conf_dir, 'pitch.conf'), mode='w') as out:
        pass


def copy_template(filename, template, recipe_path):
    d, f = os.path.split(filename)
    if not(os.path.exists(filename)):
        raise IOError(
            (
            "No {0} in {1} "
            "You need to create one adapted to "
            "your machine. You can get inspiration "
            "from {2}"
            ).format(f, d, template)
        )
    shutil.copy(filename, os.path.join(recipe_path, f))


def setup_machine_specific_scripts(recipe_path):
    kaldi_bin_dir = os.path.dirname(os.path.realpath(__file__))
    kaldi_dir = os.path.join(kaldi_bin_dir, '..', '..', 'kaldi')
    cmd_file = os.path.join(kaldi_dir, 'cmd.sh')
    cmd_template = os.path.join(kaldi_bin_dir, 'kaldi_templates', 'cmd_template.sh')
    copy_template(cmd_file, cmd_template, recipe_path)
    path_file = os.path.join(kaldi_dir, 'path.sh')
    path_template = os.path.join(kaldi_bin_dir, 'kaldi_templates', 'path_template.sh')
    copy_template(path_file, path_template, recipe_path)


def setup_main_scripts(recipe_path, run_script):
    kaldi_bin_dir = os.path.dirname(os.path.realpath(__file__))
    # score.sh
    score_file = os.path.join(kaldi_bin_dir, 'kaldi_templates', 'standard_score.sh')
    local_dir = os.path.join(recipe_path, 'local')
    if not os.path.isdir(local_dir):
        os.mkdir(local_dir)
    shutil.copy(score_file, os.path.join(local_dir, 'score.sh'))
    # run.sh
    run_file = os.path.join(kaldi_bin_dir, 'kaldi_templates', run_script)
    shutil.copy(run_file, os.path.join(recipe_path, 'run.sh'))


def setup_lm_scripts(recipe_path):
    # copy kaldi template'prepare_lm.sh' in 'recipe_path/local'
    kaldi_bin_dir = os.path.dirname(os.path.realpath(__file__))

    shutil.copy(
        os.path.join(kaldi_bin_dir, 'kaldi_templates', 'prepare_lm.sh'),
        os.path.join(recipe_path, 'local', 'prepare_lm.sh'))

    # copy custom prepare_lang.sh and validate_lang.sh scripts to
    # 'local' folder these scripts are used for models trained with
    # word_position_dependent phone variants
    shutil.copy(
        os.path.join(kaldi_bin_dir, 'kaldi_templates', 'prepare_lang_wpdpl.sh'),
        os.path.join(recipe_path, 'local', 'prepare_lang_wpdpl.sh'))

    shutil.copy(
        os.path.join(
            kaldi_bin_dir, 'kaldi_templates', 'validate_lang_wpdpl.pl'),
        os.path.join(recipe_path, 'local', 'validate_lang_wpdpl.pl'))
