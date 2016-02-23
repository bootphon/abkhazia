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
'''Provides the Abkhazia2Kaldi class'''

import os
import pkg_resources
import shutil

import abkhazia.utils as utils
import abkhazia.utils.basic_io as io


class Abkhazia2Kaldi(object):
    '''Instanciate a kaldi recipe from an abkhazia corpus

    corpus_dir : The root directory of the abkhazia corpus to
      split. This directory must contain a validated abkahzia corpus.

    recipe_dir : The output dircetory where to write the created kaldi
      recipe. A subdirectory hierarchy is created in here, as well as
      a log file.

    verbose : This argument serves as initialization of the log2file
      module. See there for more documentation.

    '''
    def __init__(self, corpus_dir, recipe_dir, verbose=False):
        # init the corpus directory
        if not os.path.isdir(corpus_dir):
            raise OSError('{} is not a directory'.format(corpus_dir))
        self.data_dir = os.path.join(corpus_dir, 'data')
        if not os.path.isdir(self.data_dir):
            raise OSError('{} is not a directory'.format(self.data_dir))

        # init the recipe directory, create it if needed
        self.recipe_dir = recipe_dir
        if not os.path.isdir(self.recipe_dir):
            os.makedirs(self.recipe_dir)

        # init the log system
        self.log = utils.log2file.get_log(
            os.path.join(self.recipe_dir, 'abkhazia2kaldi.log'), verbose)

        # init the path to kaldi
        self.kaldi_root = utils.get_config().get('kaldi', 'kaldi-directory')

        # init the path to abkhazia/share
        self.share_dir = pkg_resources.resource_filename(
            pkg_resources.Requirement.parse('abkhazia'), 'abkhazia/share')


    def _dict_path(self, name='dict'):
        """Return the directory data/local/`name`, create it if needed"""
        dict_path = os.path.join(self.recipe_dir, 'data', 'local', name)
        if not os.path.isdir(dict_path):
            os.makedirs(dict_path)
        return dict_path


    def _data_path(self, in_split=None, out_split=None):
        """Return the input and output data directories

        The returned value is a tuple (input, output) with

        input : path to the input data directory. If `in_split` is
          None, is self.data_dir. Else self.data_dir/split/`in_split`

        output : path to the output data directory. If `out_split` is
          None, is self.recipe_dir/data/main. Else
          self.recipe_dir/data/`in_split`

        """
        if in_split is None:
            inp = self.data_dir
        else:
            inp = os.path.join(self.data_dir, 'split', in_split)
        assert os.path.isdir(inp), "Directory doesn't exist: {0}".format(inp)

        if out_split is None:
            out = os.path.join(self.recipe_dir, 'data', 'main')
        else:
            out = os.path.join(self.recipe_dir, 'data', out_split)
        if not os.path.isdir(out):
            os.makedirs(out)

        return inp, out


    def _copy_template(self, filename, template):
        """Copy `filename` to self.recipe_dir"""
        path, name = os.path.split(filename)

        if not os.path.exists(filename):
            raise IOError(
                "No {0} in {1}. You need to create one adapted to "
                "your machine. You can get inspiration from {2}"
                .format(name, path, template))

        shutil.copy(filename, os.path.join(self.recipe_dir, name))


    def setup_lexicon(self, prune_lexicon=False, train_name=None, name='dict'):
        """Create data/local/`name`/lexicon.txt"""
        origin = os.path.join(self.data_dir, 'lexicon.txt')
        target = os.path.join(self._dict_path(name), 'lexicon.txt')
        self.log.debug('creating {}'.format(target))

        if prune_lexicon:
            # get words appearing in train part
            train_text = os.path.join(
                self.data_dir, 'split', train_name, 'text.txt')

            _, utt_words = io.read_text(train_text)
            allowed_words = set([word for utt in utt_words for word in utt])

            # add special OOV word <unk>
            allowed_words.add(u'<unk>')

            # remove other words from the lexicon
            allowed_words = list(allowed_words)
            io.copy_first_col_matches(origin, target, allowed_words)
        else:
            shutil.copy(origin, target)


    def setup_phone_lexicon(self, name='dict'):
        """Create data/local/`name`/lexicon.txt"""
        dict_path = self._dict_path(name)
        target = os.path.join(dict_path, 'lexicon.txt')
        self.log.debug('creating {}'.format(target))

        # get list of phones (including silence and non-silence phones)
        phones = []
        for origin in (
                os.path.join(dict_path, 'silence_phones.txt'),
                os.path.join(dict_path, 'nonsilence_phones.txt')):
            phones += [line.strip()
                       for line in utils.open_utf8(origin, 'r').xreadlines()]

        # create 'phone' lexicon
        with utils.open_utf8(target, 'w') as out:
            for word in phones:
                out.write(u'{0} {0}\n'.format(word))
            # add <unk> word, in case one wants to use the phone loop
            # lexicon for training it also is necessary if one doesn't
            # want to modify the validating scripts too much
            out.write(u'<unk> SPN\n')


    def setup_phones(self, name='dict'):
        """Create data/local/`name`/nonsilence_phones.txt"""
        origin = os.path.join(self.data_dir, 'phones.txt')
        target = os.path.join(self._dict_path(name), 'nonsilence_phones.txt')
        self.log.debug('creating {}'.format(target))

        with utils.open_utf8(target, 'w') as out:
            for line in utils.open_utf8(origin, 'r').readlines():
                symbol = line.split(u' ')[0]
                out.write(u"{0}\n".format(symbol))


    def setup_silences(self, name='dict'):
        """Create data/local/`name`/{silences, optional_silence}.txt"""
        dict_path = self._dict_path(name)
        self.log.debug('creating silences in {}'.format(dict_path))

        shutil.copy(os.path.join(self.data_dir, 'silences.txt'),
                    os.path.join(dict_path, 'silence_phones.txt'))

        target = os.path.join(dict_path, 'optional_silence.txt')
        with utils.open_utf8(target, 'w') as out:
            out.write(u'SIL\n')


    def setup_variants(self, name='dict'):
        """Create data/local/`name`/extra_questions.txt"""
        target = os.path.join(self._dict_path(name), 'extra_questions.txt')
        self.log.debug('creating {}'.format(target))

        shutil.copy(os.path.join(self.data_dir, 'variants.txt'), target)


    def setup_text(self, in_split=None, out_split=None, desired_utts=None):
        """Create text in data directory"""
        i_path, o_path = self._data_path(in_split, out_split)
        origin = os.path.join(i_path, 'text.txt')
        target = os.path.join(o_path, 'text')
        self.log.debug('creating {}'.format(target))

        if desired_utts is None:
            shutil.copy(origin, target)
        else:
            io.copy_first_col_matches(origin, target, desired_utts)


    def setup_utt2spk(self, in_split=None, out_split=None, desired_utts=None):
        """Create utt2spk in data directory"""
        i_path, o_path = self._data_path(in_split, out_split)
        origin = os.path.join(i_path, 'utt2spk.txt')
        target = os.path.join(o_path, 'utt2spk')
        self.log.debug('creating {}'.format(target))

        if desired_utts is None:
            shutil.copy(origin, target)
        else:
            io.copy_first_col_matches(origin, target, desired_utts)


    def setup_segments(self, in_split=None, out_split=None, desired_utts=None):
        """Create segments in data directory"""
        i_path, o_path = self._data_path(in_split, out_split)
        origin = os.path.join(i_path, 'segments.txt')
        target = os.path.join(o_path, 'segments')
        self.log.debug('creating {}'.format(target))

        # write only if starts and stops are specified in segments.txt
        lines = utils.open_utf8(origin, 'r').readlines()
        if len(lines[0].strip().split(u" ")) == 4:
            if desired_utts is not None:
                # select utterances that are long enough (>= 15 ms)
                lines = io.match_on_first_col(lines, desired_utts)

            with utils.open_utf8(target, 'w') as out:
                for line in lines:
                    elements = line.strip().split(u" ")
                    utt_id, wav_id = elements[:2]
                    record_id = os.path.splitext(wav_id)[0]
                    out.write(u" ".join(
                        [utt_id, record_id] + elements[2:]) + u"\n")


    def setup_wav(self, in_split=None, out_split=None, desired_utts=None):
        """Create wav.scp in data directory"""
        i_path, o_path = self._data_path(in_split, out_split)
        origin = os.path.join(i_path, 'segments.txt')
        target = os.path.join(o_path, 'wav.scp')
        self.log.debug('creating {}'.format(target))

        # get list of wavs from segments.txt
        lines = utils.open_utf8(origin, 'r').readlines()
        if desired_utts is not None:
            # select utterances that are long enough (>= 15 ms)
            lines = io.match_on_first_col(lines, desired_utts)

        # write wav.scp
        wavs = set(line.strip().split(u" ")[1] for line in lines)
        with utils.open_utf8(target, 'w') as out:
            for wav_id in wavs:
                record_id = os.path.splitext(wav_id)[0]
                path = os.path.join(
                    os.path.abspath(self.recipe_dir), 'wavs', wav_id)
                out.write(u"{0} {1}\n".format(record_id, path))


    def setup_wav_folder(self):
        # using a symbolic link to avoid copying voluminous data
        origin = os.path.join(self.data_dir, 'wavs')
        target = os.path.join(self.recipe_dir, 'wavs')
        self.log.debug('creating {}'.format(target))

        if os.path.exists(target):
            # could log this...
            os.remove(target)
        os.symlink(origin, target)


    def setup_kaldi_folders(self):
        """Create steps, utils and conf subdirectories in self.recipe_dir"""
        for target in ('steps', 'utils'):
            origin = os.path.join(self.kaldi_root, 'egs', 'wsj', 's5', target)
            target = os.path.join(self.recipe_dir, target)
            self.log.debug('creating {}'.format(target))

            if os.path.exists(target):
                os.remove(target)
            os.symlink(origin, target)

        conf_dir = os.path.join(self.recipe_dir, 'conf')
        if os.path.exists(conf_dir):
            shutil.rmtree(conf_dir)
        os.mkdir(conf_dir)

        # create mfcc.conf file (following what seems to be commonly
        # used in other kaldi recipes)
        with open(os.path.join(conf_dir, 'mfcc.conf'), mode='w') as out:
            out.write("--use-energy=false   # only non-default option.\n")

        # create empty pitch.conf file (required when using mfcc +
        # pitch features)
        with open(os.path.join(conf_dir, 'pitch.conf'), mode='w') as out:
            pass


    # TODO create cmd.sh and path.sh in share during configuration
    def setup_machine_specific_scripts(self):
        """Copy cmd.sh and path.sh to self.recipe_dir"""
        for target in ('cmd', 'path'):
            script = os.path.join(self.share_dir, target + '.sh')
            template = os.path.join(
                self.share_dir, 'kaldi_templates', target + '_template.sh')
            self._copy_template(script, template)


    def setup_main_scripts(self, run_script):
        """Copy score.sh and run.sh to self.recipe_dir"""
        # score.sh
        local_dir = os.path.join(self.recipe_dir, 'local')
        if not os.path.isdir(local_dir):
            os.mkdir(local_dir)

        score_file = os.path.join(
            self.share_dir, 'kaldi_templates', 'standard_score.sh')
        shutil.copy(score_file, os.path.join(local_dir, 'score.sh'))

        # run.sh
        run_file = os.path.join(self.share_dir, 'kaldi_templates', run_script)
        shutil.copy(run_file, os.path.join(self.recipe_dir, 'run.sh'))


    def setup_lm_scripts(self):
        """copy kaldi template 'prepare_lm.sh' in 'self.recipe_dir/local'

        Also copy custom prepare_lang.sh and validate_lang.sh scripts
        to 'local' folder. These scripts are used for models trained
        with word_position_dependent phone variants.

        """
        for target in ('prepare_lm.sh',
                       'prepare_lang_wpdpl.sh',
                       'validate_lang_wpdpl.pl'):
            shutil.copy(
                os.path.join(self.share_dir, 'kaldi_templates', target),
                os.path.join(self.recipe_dir, 'local', target))
