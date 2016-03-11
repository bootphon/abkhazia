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
import re
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
      split. This directory must contain a validated abkhazia corpus.

    recipe_dir : The output dircetory where to write the created kaldi
      recipe. A subdirectory hierarchy is created in here, as well as
      a log file.

    verbose : This argument serves as initialization of the log2file
      module. See there for more documentation.

    log : the logger to write in. default is to write in
      'self.recipe_dir'/abkhazia2kaldi.log

    When copied form abkhazia to kaldi, some files are also sorted,
    just to be sure (for example if the abkhazia corpus has been
    copied to a different machine after its creation, there might be
    some machine-dependent differences in the required orders).

    '''
    def __init__(self, corpus_dir, recipe_dir, verbose=False, log=None):
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
        self.log = (utils.log2file.get_log(
            os.path.join(self.recipe_dir, 'abkhazia2kaldi.log'), verbose)
                    if log is None else log)

        # init the path to kaldi
        self.kaldi_root = utils.config.get('kaldi', 'kaldi-directory')

        # init the path to abkhazia/share
        self.share_dir = pkg_resources.resource_filename(
            pkg_resources.Requirement.parse('abkhazia'), 'abkhazia/share')

    # TODO rename _local_path
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

    def desired_utterances(self, min_duration=0.015, njobs=1):
        """Filter out utterances too short for kaldi (less than 15ms)

        They result in empty feature files that trigger kaldi
        warnings. This is used to filter them out of the text,
        utt2spk, segments and wav.scp files.

        """
        self.log.debug('filtering out utterances shorther than 15ms')

        wav_dir = os.path.join(self.data_dir, 'wavs')
        seg_file = os.path.join(self.data_dir, 'segments.txt')
        utt_durations = io.get_utt_durations(wav_dir, seg_file, njobs)

        return [utt for utt in utt_durations
                if utt_durations[utt] >= min_duration]

    def setup_lexicon(self, train_name=None, name='dict'):
        """Create data/local/`name`/lexicon.txt"""
        # TODO see if we need to add <unk> as in setup_phone_lexicon
        origin = os.path.join(self.data_dir, 'lexicon.txt')
        target = os.path.join(self._dict_path(name), 'lexicon.txt')

        self.log.debug('creating {}'.format(target))
        shutil.copy(origin, target)
        return target

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

        return target

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

        io.cpp_sort(target)
        return target

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

    def setup_lm_scripts(self, args):
        """configure template 'prepare_lm.sh.in' in 'self.recipe_dir/local'

        Also copy custom prepare_lang.sh and validate_lang.sh scripts
        to 'local' folder. These scripts are used for models trained
        with word_position_dependent phone variants.

        """
        local = os.path.join(self.recipe_dir, 'local')
        if not os.path.isdir(local):
            os.makedirs(local)

        target = os.path.join(self.recipe_dir, 'local', 'prepare_lm.sh')
        self.configure(
            os.path.join(
                self.share_dir, 'kaldi_templates', 'prepare_lm.sh.in'),
            target, args)

        # chmod +x run.sh
        os.chmod(target, os.stat(target).st_mode | 0o111)

        for target in ('prepare_lang_wpdpl.sh', 'validate_lang_wpdpl.pl'):
            shutil.copy(
                os.path.join(self.share_dir, 'kaldi_templates', target),
                os.path.join(self.recipe_dir, 'local', target))

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

    def setup_run(self, run_script, args):
        """Configure and copy run.sh to self.recipe_dir"""
        target = os.path.join(self.recipe_dir, 'run.sh')
        origin = os.path.join(self.share_dir, 'kaldi_templates', run_script)
        self.configure(origin, target, args)

        # chmod +x run.sh
        os.chmod(target, os.stat(target).st_mode | 0o111)

    def setup_main_scripts(self, run_script, args):
        """Copy score.sh and run.sh to self.recipe_dir"""
        self.setup_score()
        self.setup_run(run_script, args)

    def configure(self, origin, target, args, expr='@@@@'):
        """Configure the file 'target' from 'origin' and 'args'

        Replace the lines starting with param='expr' in 'origin' by
        param=args.param, do not touch the unmatched lines and copy
        the whole in 'target'. Raises IOError if args.param does not
        exist.

        """
        self.log.debug('configuring {} to {}'
                       .format(os.path.basename(origin), target))

        with utils.open_utf8(target, 'w') as out:
            for line in utils.open_utf8(origin, 'r').readlines():
                matched = re.match('.*=' + expr, line)
                if matched and not line.startswith('#'):
                    # parameter name from the file
                    param = matched.group().split('=')[0].strip()
                    try:
                        # parameter value from args
                        value = vars(args)[param]
                    except KeyError:
                        out.close()
                        utils.remove(out.name)
                        raise IOError(
                            "'{}' parameter is requested but not defined"
                            .format(param))

                    line = param + '=' + str(value).lower() + '\n'
                    self.log.debug('configured ' + line[:-1])
                out.write(line)
