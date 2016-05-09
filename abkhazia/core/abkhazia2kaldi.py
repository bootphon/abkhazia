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
# along with abkhazia. If not, see <http://www.gnu.org/licenses/>.
'''Provides the Abkhazia2Kaldi class'''

import os
import pkg_resources
import shutil

import abkhazia.utils as utils
import abkhazia.utils.basic_io as io


# TODO comment !
def add_argument(parser, section, name, type, help,
                 metavar=None, choices=None):
    if metavar is None:
        try:
            metavar = {
                bool: '<true|false>',
                float: '<float>',
                int: '<int>'
            }[type]
        except KeyError:
            metavar = '<' + name + '>'

    if type is bool:
        parser.add_argument(
            '--'+name, choices=['true', 'false'], metavar=metavar,
            default=utils.config.get(section, name),
            help=help + ' (default is %(default)s)')
    elif choices is None:
        parser.add_argument(
            '--'+name, type=type, metavar=metavar,
            default=utils.config.get(section, name),
            help=help + ' (default is %(default)s)')
    else:
        parser.add_argument(
            '--'+name, type=type, choices=choices, metavar=metavar,
            default=utils.config.get(section, name),
            help=help + ' (default is %(default)s)')


class Abkhazia2Kaldi(object):
    '''Instanciate a kaldi recipe from an abkhazia corpus

    corpus_dir : The root directory of the abkhazia corpus to
      read from. This directory must contain a valid abkhazia corpus

    recipe_dir : The output dircetory where to write the created kaldi
      recipe. A subdirectory hierarchy is created in here

    name : The name of the recipe in the directory hierarchy, default
      is 'recipe'.

    verbose : This argument serves as initialization of the log2file
      module. See there for more documentation

    log : the logger to write in. default is to write in
      'self.recipe_dir'/abkhazia2kaldi.log

    When copied form abkhazia to kaldi, some files are also sorted,
    just to be sure (for example if the abkhazia corpus has been
    copied to a different machine after its creation, there might be
    some machine-dependent differences in the required orders).

    '''
    def __init__(self, corpus_dir, recipe_dir,
                 name='recipe', verbose=False, log=None):
        self.verbose = verbose

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

        # init the recipe name
        self.name = name

        # init the log system
        self.log = (utils.log2file.get_log(
            os.path.join(self.recipe_dir, 'abkhazia2kaldi.log'), verbose)
                    if log is None else log)

        # init the path to kaldi
        self.kaldi_root = utils.config.get('kaldi', 'kaldi-directory')

        # init the path to abkhazia/share
        self.share_dir = pkg_resources.resource_filename(
            pkg_resources.Requirement.parse('abkhazia'), 'abkhazia/share')

    def _local_path(self):
        """Return the directory data/local/self.name, create it if needed"""
        dict_path = os.path.join(self.recipe_dir, 'data', 'local', self.name)
        if not os.path.isdir(dict_path):
            os.makedirs(dict_path)
        return dict_path

    def _data_path(self, in_split=None, out_split=None):
        """Return the input and output data directories

        The returned value is a tuple (input, output) with

        input : path to the input data directory. If `in_split` is
          None, is self.data_dir. Else self.data_dir/split/`in_split`

        output : path to the output data directory. If `out_split` is
          None, is self.recipe_dir/data/self.name. Else
          self.recipe_dir/data/`in_split`

        """
        if in_split is None:
            inp = self.data_dir
        else:
            inp = os.path.join(self.data_dir, 'split', in_split)
        assert os.path.isdir(inp), "directory doesn't exist: {0}".format(inp)

        final_dir = self.name if out_split is None else out_split
        out = os.path.join(self.recipe_dir, 'data', final_dir)
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

    def desired_utterances(self, min_duration=0.015, njobs=1):
        """Filter out utterances too short for kaldi (less than 15ms)

        They result in empty feature files that trigger kaldi
        warnings. This is used to filter them out of the text,
        utt2spk, segments and wav.scp files.

        """
        self.log.debug('filtering out utterances shorther than 15ms')

        wav_dir = os.path.join(self.data_dir, 'wavs')
        seg_file = os.path.join(self.data_dir, 'segments.txt')
        utt_durations = io.get_utt_durations(wav_dir, seg_file, njobs, self.verbose)

        return [utt for utt in utt_durations
                if utt_durations[utt] >= min_duration]

    def setup_lexicon(self, train_name=None):
        """Create data/local/self.name/lexicon.txt"""
        # TODO see if we need to add <unk> as in setup_phone_lexicon
        origin = os.path.join(self.data_dir, 'lexicon.txt')
        target = os.path.join(self._local_path(), 'lexicon.txt')

        self.log.debug('creating {}'.format(target))
        shutil.copy(origin, target)
        return target

    def setup_phone_lexicon(self):
        """Create data/local/self.name/lexicon.txt"""
        local_path = self._local_path()
        target = os.path.join(local_path, 'lexicon.txt')
        self.log.debug('creating {}'.format(target))

        # get list of phones (including silence and non-silence phones)
        phones = []
        for origin in (
                os.path.join(local_path, 'silence_phones.txt'),
                os.path.join(local_path, 'nonsilence_phones.txt')):
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

        return target

    def setup_phones(self):
        """Create data/local/self.name/nonsilence_phones.txt"""
        origin = os.path.join(self.data_dir, 'phones.txt')
        target = os.path.join(self._local_path(), 'nonsilence_phones.txt')
        self.log.debug('creating {}'.format(target))

        with utils.open_utf8(target, 'w') as out:
            for line in utils.open_utf8(origin, 'r').readlines():
                symbol = line.split(u' ')[0]
                out.write(u"{0}\n".format(symbol))

    def setup_silences(self):
        """Create data/local/self.name/{silences, optional_silence}.txt"""
        local_path = self._local_path()
        self.log.debug('creating silences in {}'.format(local_path))

        shutil.copy(os.path.join(self.data_dir, 'silences.txt'),
                    os.path.join(local_path, 'silence_phones.txt'))

        target = os.path.join(local_path, 'optional_silence.txt')
        with utils.open_utf8(target, 'w') as out:
            out.write(u'SIL\n')

    def setup_variants(self):
        """Create data/local/`name`/extra_questions.txt"""
        target = os.path.join(self._local_path(), 'extra_questions.txt')
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

        io.cpp_sort(target)
        return target

    def setup_utt2spk(self, in_split=None, out_split=None, desired_utts=None):
        """Create utt2spk and spk2utt in data directory"""
        i_path, o_path = self._data_path(in_split, out_split)
        origin = os.path.join(i_path, 'utt2spk.txt')
        target = os.path.join(o_path, 'utt2spk')
        self.log.debug('creating {}'.format(target))

        if desired_utts is None:
            shutil.copy(origin, target)
        else:
            io.copy_first_col_matches(origin, target, desired_utts)
        io.cpp_sort(target)

        # create spk2utt
        origin = target
        target = os.path.join(o_path, 'spk2utt')
        self.log.debug('creating {}'.format(target))
        utils.spk2utt(origin, target)
        io.cpp_sort(target)

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

        io.cpp_sort(target)

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

        io.cpp_sort(target)

    def setup_wav_folder(self):
        """using a symbolic link to avoid copying voluminous data"""
        origin = os.path.abspath(os.path.join(self.data_dir, 'wavs'))
        target = os.path.join(self.recipe_dir, 'wavs')

        if os.path.exists(target):
            self.log.debug('overwriting {}'.format(target))
            os.remove(target)
        else:
            self.log.debug('creating {}'.format(target))
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

    def setup_machine_specific_scripts(self):
        """Copy cmd.sh and path.sh to self.recipe_dir"""
        for target in ('cmd', 'path'):
            script = os.path.join(self.share_dir, target + '.sh')
            template = os.path.join(
                self.share_dir, 'kaldi_templates', target + '_template.sh')
            self._copy_template(script, template)

    def setup_score(self):
        """Copy score.sh to self.recipe_dir"""
        local_dir = os.path.join(self.recipe_dir, 'local')
        if not os.path.isdir(local_dir):
            os.mkdir(local_dir)

        shutil.copy(
            os.path.join(
                self.share_dir, 'kaldi_templates', 'standard_score.sh'),
            os.path.join(local_dir, 'score.sh'))