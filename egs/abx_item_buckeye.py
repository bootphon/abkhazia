#!/usr/bin/env python
#
# Copyright 2016 Mathieu Bernard
#
# You can redistribute this program and/or modify it under the terms
# of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
import argparse
import os
import sys
import tempfile

import abkhazia.corpus.prepare.buckeye_preparator as buckeye
import abkhazia.utils as utils
from utils.abkhazia2abx import alignment2item


# The path to the raw Buckeye distribution
BUCKEYE_RAW = '/fhgfs/bootphon/data/raw_data/BUCKEYE_revised_bootphon'


def main():
    # define and parse input arguments
    parser = argparse.ArgumentParser(
        description='Generate an ABX item file from the Buckeye corpus')
    parser.add_argument(
        'item_file', metavar='ITEM_FILE', help='item file to be generated')
    parser.add_argument(
        '-b', '--buckeye-dir', default=BUCKEYE_RAW,
        help='path to the raw Buckeye corpus to prepare'
        ', default is %(default)s')
    parser.add_argument(
        '-t', '--tmp-dir', default=tempfile.gettempdir(),
        help='temporary directory to use, default is %(default)s')
    args = parser.parse_args()

    # setup the log and tmpdir
    tmpdir = tempfile.mkdtemp(dir=args.tmp_dir)
    log = utils.logger.get_log(verbose=False, header_in_stdout=False)

    try:
        # import Buckeye in abkhazia format
        corpus = buckeye.BuckeyePreparator(args.buckeye_dir, log=log).prepare(
            os.path.join(tmpdir, 'wavs'),
            keep_short_utts=False)

        # remove undesired utterances (text is '<IVER>'). Few of those
        # utts cause the alignment step to bug... and in all case they are
        # useless. TODO find that bug!
        _len = len(corpus.utts())
        corpus = corpus.subcorpus(
            [u for u in corpus.utts() if corpus.text[u] != '<IVER>'])
        log.info('removed %s utterances containing only "<IVER>"',
                 _len - len(corpus.utts()))

        # get the manual phones alignment from the raw buckeye
        log.info('extracting manual alignments at phone level...')
        get_alignment = buckeye.GetAlignment(args.buckeye_dir)
        alignment = {}
        for utt in corpus.utts():
            record, tstart, tstop = corpus.segments[utt]
            alignment[utt] = get_alignment(record, tstart, tstop)

        # save the alignment
        alignment_file = os.path.join(tmpdir, 'alignment.txt')
        open(alignment_file, 'w').write(
            '\n'.join(
                '{} {} {} {}'.format(utt, p[0], p[1], p[2])
                for utt, phones in alignment.items()
                for p in phones))

        log.info('generating the item file...')
        alignment2item(
            corpus, alignment_file, args.item_file,
            verbose=1, njobs=1)

    finally:
        # cleanup temp directory
        utils.remove(tmpdir)


if __name__ == '__main__':
    sys.exit(main())
