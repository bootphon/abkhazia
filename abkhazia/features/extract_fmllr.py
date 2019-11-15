"""Transforms raw features into fMLLR features

This function is inspired from kaldi/egs/wsj/s5/steps/decode_fmllr.sh.

"""

import os
import subprocess

from abkhazia.kaldi.path import kaldi_path
from abkhazia.utils.path import list_directory


def extract_fmllr(corpus_dir, feat_dir, trans_dir, output_dir):
    """Creates fMLLR features from raw features and fMLLR transforms

    The function applies fMLLR transfroms computed during speaker adapted
    acoustic modeling, alignment or decoding step (stored in `trans_dir`) to a
    set of features (stored in `feat_dir`).

    Creates fmllr.ark and fmllr.scp in `output_dir`

    Parameters
    ----------
    corpus_dir : directory
        The directory storing the original corpus, requires
        the file `corpus_dir`/utt2spk.txt.
    feat_dir : directory
        The directory storing raw features, must be computed WITH cmvn and
        WITHOUT deltas. Requires the files `feats_dir`/{cmvn.scp, feats.scp}.
    trans_dir : directory
        The directory storing the fMLLR transforms computed on the same
        features, usually a triphone-sa acoustic model, requires the files
        `trans_dir`/{trans.*}.
    output_dir : directory
        The directory where to write `fmllr.ark` and `fmllr.scp`, must exists.

    Raises
    ------
    ValueError
        If a required input file is not found or if the computation failed.

    """
    output_dir = os.path.abspath(output_dir)
    if not os.path.isdir(output_dir):
        raise ValueError(f'{output_dir} is not a directory')

    utt2spk = os.path.join(corpus_dir, 'utt2spk.txt')
    cmvn_scp = os.path.join(feat_dir, 'cmvn.scp')
    feats_scp = os.path.join(feat_dir, 'feats.scp')
    for f in (utt2spk, cmvn_scp, feats_scp):
        if not os.path.isfile(f):
            raise ValueError(f'file not found {f}')

    trans_files = [
        f for f in list_directory(trans_dir, abspath=True) if '/trans.' in f]
    if not trans_files:
        raise ValueError(f'no trans.* files in {trans_dir}')

    try:
        # merge all the trans_files in a single temporary file
        tmp = open(os.path.join(output_dir, 'trans'), 'w+b')
        for f in sorted(trans_files):
            tmp.write(open(f, 'rb').read())
        tmp.close()

        # commands to extract fMLLR features
        utt2spk = f'--utt2spk=ark:{utt2spk}'
        command1 = f'apply-cmvn {utt2spk} scp:{cmvn_scp} scp:{feats_scp} ark:-'
        command2 = f'add-deltas ark:- ark:-'
        command3 = (
            f'transform-feats {utt2spk} ark:{tmp.name} ark:- '
            f'ark,scp:{output_dir}/fmllr.ark,{output_dir}/fmllr.scp')
        command = ' | '.join((command1, command2, command3))

        # execute the command
        try:
            subprocess.run(command, shell=True, check=True, env=kaldi_path())
        except subprocess.CalledProcessError:
            raise ValueError('failed to compute fMLLR features')
    finally:
        os.remove(os.path.join(output_dir, 'trans'))
