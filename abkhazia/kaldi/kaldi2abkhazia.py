# Copyright 2015, 2016 Thomas Schatz
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
"""Exporting forced alignments from kaldi to abkhazia"""

from abkhazia.utils import open_utf8

def read_kaldi_phonemap(phones_file, word_position_dependent=True):
    phonemap = {}
    for line in open_utf8(phones_file, 'r').xreadlines():
        phone, code = line.strip().split(u" ")
        # remove word position markers
        if word_position_dependent:
            if phone[-2:] in ["_I", "_B", "_E", "_S"]:
                phone = phone[:-2]
        phonemap[code] = phone
    return phonemap


def read_kaldi_alignment(phonemap,  tra_file):
    # tra_file using the format on each line: utt_id [phone_code
    # n_frames]+ this is a generator (it yields in the loop)
    for line in open_utf8(tra_file, 'r').xreadlines():
        sequence = line.strip().split(u" ; ")
        utt_id, code, nframes = sequence[0].split(u" ")
        sequence = [u" ".join([code, nframes])] + sequence[1:]
         # this seems good enough, but I (Thomas) didn't check in the
         # make_mfcc code of kaldi to be sure
        start = 0.0125

        for elem in sequence:
            code, nframes = elem.split(u" ")
            stop = start + 0.01*int(nframes)
            yield utt_id, start, stop, phonemap[code]
            start = stop


# TODO check alignment: which utt have been transcribed, have silence
# been inserted, otherwise no difference? (maybe some did not reach
# final state), chronological order, grouping by utt_id etc.
def export_phone_alignment(phones_file, tra_file, out_file,
                           word_position_dependent=True):
    # phone file: phones.txt in lang_dir, tra_file: in export
    phonemap = read_kaldi_phonemap(phones_file, word_position_dependent)
    with open_utf8(out_file, 'w') as out:
        for utt_id, start, stop, phone in read_kaldi_alignment(phonemap, tra_file):
            out.write(u"{0} {1} {2} {3}\n".format(utt_id, start, stop, phone))
