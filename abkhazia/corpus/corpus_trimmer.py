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
"""Provides the CorpusTrimmer class"""

import os
import shutil
import subprocess
import shlex
import sys
import wave
import contextlib

from itertools import *
from operator import itemgetter, attrgetter, methodcaller
from collections import defaultdict
from abkhazia.utils import open_utf8, logger


class CorpusTrimmer(object):
    """Removes utterances from a corpus"""

    def __init__(self, corpus, log=logger.null_logger()):
        """Removes utterances in 'not_kept_utts' from the
        wavs in the corpus

        'corpus' is an instance of Corpus'

        'not_kept_utts' is a dictionnary of the form :
        not_kept_utts=(speaker :[(utt1,wav_id,start_time,stop_time),
        (utt1,wav_id,start_time,stop_time)...])
        """
        self.log = log
        self.corpus = corpus

        utt_ids, utt_speakers = list(zip(*self.corpus.utt2spk.items()))
        self.utts = list(zip(utt_ids, utt_speakers))
        self.speakers = set(utt_speakers)

    def trim(self, corpus_dir, output_dir, function, not_kept_utts):
        """Given a corpus and a list of utterances, this
        method removes the utterances in the list from the wavs,
        from segments, from the text and from utt2spk
        """
        # return error if sox is not installed
        try:
            subprocess.check_output(shlex.split('which sox'))
        except:
            raise OSError('sox is not installed on your system')

        spk2utts = defaultdict(list)
        for utt, spkr in self.utts:
            spk2utts[spkr].append(utt)

        # get input and output wav paths
        corpus_dir = os.path.abspath(corpus_dir)
        wav_dir = self.corpus.wav_folder
        if not os.path.isdir(wav_dir):
            raise IOError('invalid corpus: not found{}'.format(path))

        output_dir = os.path.abspath(output_dir)
        output_dir = os.path.join(output_dir, function)
        output_wav_dir = os.path.join(output_dir, 'data/wavs')
        if not os.path.isdir(output_wav_dir):
            os.makedirs(output_wav_dir)

        # remove utterances from the wavs using sox
        for speaker in self.speakers:
            print(speaker)
            utt_to_remove = not_kept_utts[speaker]

            # if speaker doesn't have utt to remove, copy file
            if utt_to_remove == []:
                wavs_to_copy = set([self.corpus.segments[utt][0] for
                                    utt in spk2utts[speaker]])
                for wav in wavs_to_copy:
                    wav_name = '.'.join([wav, 'wav'])
                    wav_input_path = '/'.join([wav_dir, wav_name])
                    wav_output_path = '/'.join([output_wav_dir, wav_name])

                    shutil.copyfile(wav_input_path, wav_output_path)

            # don't trim utterances for wave file that won't be kept at all
            wav_ids = [os.path.splitext(w)[0] for w in self.corpus.wavs]
            wavs_output = [(wav_id, start, stop)
                           for utt_id, (wav_id, start, stop)
                           in utt_to_remove if wav_id in wav_ids]

            wavs_start_dict = defaultdict(list)
            wavs_stop_dict = defaultdict(list)
            wavs_duration_dict = defaultdict(list)
            for wav_id, start, stop in wavs_output:
                wavs_start_dict[wav_id].append(start)
                wavs_stop_dict[wav_id].append(stop)
                wavs_duration_dict[wav_id].append(stop - start)

            for wav in wavs_start_dict:
                # start removing utterances at the end
                # and finish at the begining : removing an utterance at the
                # end doesn't affect the other utterances timestamps !
                wavs_starts_temp = sorted(wavs_start_dict[wav], reverse=True)
                wavs_stop_temp = sorted(wavs_stop_dict[wav], reverse=True)

                wav_name = '.'.join([wav, 'wav'])
                wav_input_path = '/'.join([wav_dir, wav_name])
                wav_output_path = '/'.join([output_wav_dir, wav_name])

                # Create string of timestamps to remove to pass as
                # arguments to sox
                timestamps = ''
                for start, stop in zip(wavs_starts_temp, wavs_stop_temp):
                    times = '=' + str(start) + ' ' + '=' + str(stop)
                    timestamps = ' '.join([times, timestamps])

                # call sox to trim part of the signal
                list_command = ['sox', wav_input_path,
                                wav_output_path, 'trim 0', timestamps]

                command = ' '.join(list_command)
                process = subprocess.Popen(
                        shlex.split(command), stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()
                if stdout:
                    self.log.debug(stdout)
                if stderr:
                    self.log.debug(stderr)

                self.log.debug(
                        '''for wav {wav_id}, {duration} seconds'''
                        '''should have been trimmed'''.format(
                            wav_id=wav, duration=sum(wavs_duration_dict[wav])))

                # if the output file is empty, remove it
                with contextlib.closing(
                        wave.open(wav_output_path, 'r')) as wav_file:
                    frames = wav_file.getnframes()

                self.log.debug('checking length of output trimmed file')
                if frames == 0:
                    self.log.debug(
                            'removing empty file : {wav_id}'.format(
                                wav_id=wav_output_path))
                    os.remove(wav_output_path)
