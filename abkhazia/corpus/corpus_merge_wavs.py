# -*- coding: utf-8 -*-
"""
Created on Wed Nov  1 04:38:30 2017

@author: Thomas Schatz
"""

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
"""Provides the CorpusMergeWavs class"""


import os
import wave
import contextlib
import numpy as np
import array

from abkhazia.utils import logger


#FIXME: this won't work for corpora with several speakers per wavefile
#FIXME modifying original corpus in place could lead to undesirable
# side-effects. Better to use a copy
class CorpusMergeWavs:
    """A class for merging the wavs files together for each speaker,
    at the end of this class, one .wav file = one speaker. This
    class also adjusts segments.txt to match the new wavs.


    corpus : The abkhazia corpus to filter. The corpus is assumed
      to be valid.

    log : A logging.Logger instance to send log messages

    function : A string that specifies the cutting function that
      will be used on the corpus

    plot : A boolean which, if set to true, enables the plotting
      of the speech distribution and the cutting function
    """


    def __init__(self, corpus, log=logger.null_logger()):
        self.log = log
        self.corpus = corpus
        # read utt2spk from the input corpus
        utt_ids, utt_speakers = zip(*self.corpus.utt2spk.items())
        self.utts = zip(utt_ids, utt_speakers)
        self.size = len(utt_ids)
        self.speakers = set(utt_speakers)
        self.segments = self.corpus.segments
        self.utt2dur = self.corpus.utt2duration()
        self.log.debug('loaded %i utterances from %i speakers',
                       self.size, len(self.speakers))


    def get_wav_duration(self, wav):
        with contextlib.closing(wave.open(wav, 'r')) as wav_file:
            frames = wav_file.getnframes()
            rate = wav_file.getframerate()
        duration = frames / float(rate)
        self.log.debug('wav file {} has a duration of {}'.format(wav,
                                                                 duration))
        return duration


    def get_per_spk_data(self):
        # get following corpus info per speaker:
        #   total duration
        #   list of wavs
        #   list of wav durs
        #   list of utts
        self.spk_data = {'total_dur': {}, 'wavs': {}, 'wav_durs': {}, 'utts': {}}
        for spkr in self.speakers:
            spk_utts = [utt_id for utt_id, utt_speaker in self.utts
                                if utt_speaker == spkr]
            duration = sum([self.utt2dur[utt_id] for utt_id in spk_utts])
            self.spk_data['total_dur'][spkr] = duration
            self.spk_data['utts'][spkr] = spk_utts
            self.log.debug('for speaker {}, total duration is {}'.format(
                            spkr, duration/60))
            wavs = [self.segments[utt][0]
                        for utt in self.spk_data['utts'][spkr]]
            # we want unique values in the list of wavs:
            wavs = sorted(list(set(wavs)))
            self.spk_data['wavs'][spkr] = wavs
            self.spk_data['wav_durs'][spkr] = []
            for wav in wavs:
                wav_path = os.path.join(self.corpus.wav_folder, wav)
                duration = self.get_wav_duration(wav_path)
                self.spk_data['wav_durs'][spkr].append(duration)


    def merge_wavs(self, output_dir, padding=0.):
        """
        Merge wav files to have 1 wav per speaker
        and modify accordingly segments to have correct
        timestamps for each utterance

        output_dir : path to 'data' folder where resulting corpus is saved

        padding : duration of silence inserted between merged wave files
                  (in seconds)
        """
        # get input and output wav dir
        wav_output_dir = os.path.join(output_dir, 'wavs')
        wav_dir = self.corpus.wav_folder
        if not os.path.isdir(wav_dir):
            raise IOError('invalid corpus: {} not found'.format(wav_dir))
        if not os.path.isdir(wav_output_dir):
            os.makedirs(wav_output_dir)

        # get some corpus info per speaker
        self.get_per_spk_data()

        # generate new segment file
        expected_duration = {}
        for spkr in self.speakers:
            #the name of the final wave file will be spkr.wav (ex s01.wav)
            spk_wav_id = spkr + '.wav'
            # offset for each wav of given speaker
            wav_durs = [e+padding for e in self.spk_data['wav_durs'][spkr]]
            cumdurs = list(np.cumsum(wav_durs))
            expected_duration[spk_wav_id] = cumdurs[-1] - padding
            offsets = {e : f for e, f in zip(self.spk_data['wavs'][spkr], [0]+cumdurs[:-1])}
            for utt in self.spk_data['utts'][spkr]:
                utt_wav = self.segments[utt][0]
                offset = offsets[utt_wav]
                if self.segments[utt][1] is not None:
                    start = self.segments[utt][1]
                    stop = self.segments[utt][2]
                else:
                    # if the corpus has 1 wav file per utt, segments.txt
                    # doesn't list the timestamps.
                    start = 0.
                    stop = self.utt2dur[utt]
                self.segments[utt] = spk_wav_id, start+offset, stop+offset

        # update segments in original corpus
        self.corpus.segments = self.segments

        #merge the wavs
        for spkr in self.speakers:
            # create the list of waves we want to merge
            wav_name = spkr + '.wav'
            in_wavs = [os.path.join(self.corpus.wav_folder, wav)
                        for wav in self.spk_data['wavs'][spkr]]
            out_wav = os.path.join(wav_output_dir, wav_name)
            # read in wavs
            waveforms = []
            prev_params = None
            for wav in in_wavs:
                with contextlib.closing(wave.open(wav, 'r')) as wav_file:
                    (nchan, b, fs, n, comp_T, comp_N) = wav_file.getparams()
                    waveform = wav_file.readframes(n)
                if not(prev_params is None):
                    assert prev_params == (nchan, b, fs, comp_T, comp_N)
                prev_params = (nchan, b, fs, comp_T, comp_N)
                waveforms.append(waveform)
            # prepare zero padding
            if padding > 0:
                pad_frames = int(round(fs*padding))
                assert b == 2
                pad = array.array('h', [0]*pad_frames).tostring()
            # write out wav
            with contextlib.closing(wave.open(out_wav, 'w')) as wav_file:
                wav_file.setparams((nchan, b, fs, 0, comp_T, comp_N))
                for i, waveform in enumerate(waveforms):
                    # writeframes also updates nbframes
                    wav_file.writeframes(waveform)
                    if padding > 0 and i+1 < len(waveforms):
                        wav_file.writeframes(pad)

        # update wave set
        self.corpus.wav_folder = wav_output_dir
        self.corpus.wavs = {spkr+'.wav' for spkr in self.speakers}

        # check that created file length is what we expect
        for wav in self.corpus.wavs:
            wav_file = os.path.join(self.corpus.wav_folder, wav)
            duration = self.get_wav_duration(wav_file)
            print(duration)
            print(expected_duration[wav])
            assert abs(duration - expected_duration[wav]) < 1e-5, \
                    "Unexpected merged file duration"

        # validate the corpus
        self.corpus.validate()

        # save corpus
        self.corpus.save(output_dir, no_wavs=True)  # wavs are already there
