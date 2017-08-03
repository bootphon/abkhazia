# Copyright 2015, 2016 Thomas Schatz, Xuan-Nga Cao, Mathieu Bernard
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

from abkhazia.utils import config, logger, open_utf8
from abkhazia.corpus.corpus_saver import CorpusSaver


class Abkhazia2Kaldi(object):
    '''Instanciate a kaldi recipe from an abkhazia corpus

    corpus : An abkhazia corpus

    recipe_dir : The output dircetory where to write the created kaldi
      recipe. A subdirectory hierarchy is created in here

    name : The name of the recipe in the directory hierarchy, default
      is 'recipe'.

    log : the logger to write in

    When copied form abkhazia to kaldi, some files are also sorted,
    just to be sure (for example if the abkhazia corpus has been
    copied to a different machine after its creation, there might be
    some machine-dependent differences in the required orders).

    '''
    def __init__(self, corpus, recipe_dir,
                 name='recipe', log=logger.null_logger()):
        # filter out short utterances
        self.corpus = corpus.subcorpus(
            self._desired_utterances(corpus), validate=False)

        # init the recipe directory, create it if needed
        self.recipe_dir = recipe_dir
        if not os.path.isdir(self.recipe_dir):
            os.makedirs(self.recipe_dir)

        self.name = name
        self.log = log

        # init the path to kaldi
        self.kaldi_root = config.get('kaldi', 'kaldi-directory')

        # init the path to abkhazia/share
        self.share_dir = pkg_resources.resource_filename(
            pkg_resources.Requirement.parse('abkhazia'), 'abkhazia/share')

    def _local_path(self):
        """Return the directory data/local/self.name, create it if needed"""
        dict_path = os.path.join(self.recipe_dir, 'data', 'local', self.name)
        if not os.path.isdir(dict_path):
            os.makedirs(dict_path)
        return dict_path

    def _output_path(self):
        out = os.path.join(self.recipe_dir, 'data', self.name)
        if not os.path.isdir(out):
            os.makedirs(out)
        return out

    @staticmethod
    def _desired_utterances(corpus, min_duration=0.015):
        """Filter out utterances too short for kaldi (less than 15ms)

        They result in empty feature files that trigger kaldi
        warnings. This is used to filter them out of the text,
        utt2spk, segments and wav.scp files.

        """
        # TODO we have already that somewhere in validator (or in
        # features?)
        return [utt for utt, dur in corpus.utt2duration().iteritems()
                if dur >= min_duration]

    def setup_lexicon(self):
        """Create data/local/self.name/lexicon.txt"""
        target = os.path.join(self._local_path(), 'lexicon.txt')
        CorpusSaver.save_lexicon(self.corpus, target)
        return target

    # def setup_phone_lexicon(self):
    #     """Create data/local/self.name/lexicon.txt"""
    #     local_path = self._local_path()
    #     target = os.path.join(local_path, 'lexicon.txt')

    #     # get list of phones (including silence and non-silence phones)
    #     phones = []
    #     for origin in (
    #             os.path.join(local_path, 'silence_phones.txt'),
    #             os.path.join(local_path, 'nonsilence_phones.txt')):
    #         phones += [line.strip()
    #                    for line in open_utf8(origin, 'r').xreadlines()]

    #     # create 'phone' lexicon
    #     with open_utf8(target, 'w') as out:
    #         for word in phones:
    #             out.write(u'{0} {0}\n'.format(word))
    #         # add <unk> word, in case one wants to use the phone loop
    #         # lexicon for training it also is necessary if one doesn't
    #         # want to modify the validating scripts too much
    #         out.write(u'<unk> SPN\n')

    #     return target

    def setup_phones(self):
        """Create data/local/self.name/nonsilence_phones.txt"""
        target = os.path.join(self._local_path(), 'nonsilence_phones.txt')
        with open_utf8(target, 'w') as out:
            for symbol in self.corpus.phones.iterkeys():
                out.write(u"{0}\n".format(symbol))

    def setup_silences(self):
        """Create data/local/self.name/{silences, optional_silence}.txt"""
        local_path = self._local_path()
        CorpusSaver.save_silences(
            self.corpus, os.path.join(local_path, 'silence_phones.txt'))

        target = os.path.join(local_path, 'optional_silence.txt')
        with open_utf8(target, 'w') as out:
            out.write(u'SIL\n')

    def setup_variants(self):
        """Create data/local/`name`/extra_questions.txt"""
        target = os.path.join(self._local_path(), 'extra_questions.txt')
        CorpusSaver.save_variants(self.corpus, target)

    def setup_text(self):
        """Create text in data directory"""
        target = os.path.join(self._output_path(), 'text')
        CorpusSaver.save_text(self.corpus, target)

    def setup_utt2spk(self):
        """Create utt2spk and spk2utt in data directory"""
        target = os.path.join(self._output_path(), 'utt2spk')
        CorpusSaver.save_utt2spk(self.corpus, target)

        # create spk2utt
        target = os.path.join(self._output_path(), 'spk2utt')
        with open_utf8(target, 'w') as out:
            for spk, utt in sorted(self.corpus.spk2utt().iteritems()):
                out.write(u'{} {}\n'.format(spk, ' '.join(sorted(utt))))

    def setup_segments(self,):
        """Create segments in data directory"""
        target = os.path.join(self._output_path(), 'segments')
        # write only if starts and stops are specified in segments.txt
        if self.corpus.has_several_utts_per_wav():
            CorpusSaver.save_segments(self.corpus, target)

    def setup_wav(self):
        """Create wav.scp in data directory"""
        target = os.path.join(self._output_path(), 'wav.scp')
        wavs = set(w for w, _, _ in self.corpus.segments.itervalues())
        with open_utf8(target, 'w') as out:
            for wav in sorted(wavs):
                wav_path = os.path.join(self.corpus.wav_folder, wav)
                out.write(u'{} {}\n'.format(wav, wav_path))

    def setup_wav_folder(self):
        """using a symbolic link to avoid copying voluminous data"""
        target = os.path.join(self.recipe_dir, 'wavs')
        CorpusSaver.save_wavs(self.corpus, target)

    def setup_kaldi_folders(self):
        """Create steps, utils and conf subdirectories in self.recipe_dir"""
        for target in ('steps', 'utils'):
            origin = os.path.join(self.kaldi_root, 'egs', 'wsj', 's5', target)
            target = os.path.join(self.recipe_dir, target)

            if os.path.exists(target):
                os.remove(target)
            os.symlink(origin, target)

    @staticmethod
    def _write_cmd_script(script):
        with open(script, 'w') as stream:
            for cmd in ('train', 'decode', 'highmem'):
                key = '{}-cmd'.format(cmd)
                value = config.get('kaldi', key)
                stream.write('export {}={}\n'.format(key, value))

    @staticmethod
    def _write_path_script(script):
        source = pkg_resources.resource_filename(
            pkg_resources.Requirement.parse('abkhazia'),
            'abkhazia/share/path.sh')
        shutil.copy(source, script)

    def setup_machine_specific_scripts(self):
        """Setup cmd.sh and path.sh in self.recipe_dir"""
        self._write_cmd_script(os.path.join(self.recipe_dir, 'cmd.sh'))
        self._write_path_script(os.path.join(self.recipe_dir, 'path.sh'))

    def setup_score(self):
        """Copy kaldi/egs/wsj/s5/local/score.sh to self.recipe_dir"""
        local_dir = os.path.join(self.recipe_dir, 'local')
        if not os.path.isdir(local_dir):
            os.mkdir(local_dir)

        origin = os.path.join(
            self.kaldi_root, 'egs', 'wsj', 's5', 'local', 'score.sh')
        assert os.path.isfile(origin), 'no such file {}'.format(origin)

        target = os.path.join(local_dir, 'score.sh')
        shutil.copy(origin, target)
