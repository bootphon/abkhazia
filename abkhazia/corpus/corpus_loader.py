# Copyright 2016 Thomas Schatz, Xuan Nga Cao, Mathieu Bernard
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
"""Load an abkhazia corpus from disk"""

import os
import abkhazia.utils as utils


class CorpusLoader(object):
    """Load an abkhazia corpus from a directory

    This class provides static methods for accessing corpus data in a
    directory. The `load()` method initialize a whole corpus and
    return it as a Corpus instance. Other (specialized) methods return
    only part of a corpus.

    """

    @classmethod
    def load(cls, corpus_cls, corpus_dir):
        """Return a corpus initialized from `corpus_dir`

        Raise IOError if corpus_dir if an invalid abkhazia corpus
        directory.

        """
        # get the corpus data files as dict basename -> abspath
        data = cls._load_corpus_dir(corpus_dir)

        # init the corpus from data files
        corpus = corpus_cls()
        corpus.wavs = cls.load_wavs(data['wavs'])
        corpus.lexicon = cls.load_lexicon(data['lexicon'])
        corpus.segments = cls.load_segments(data['segments'])
        corpus.text = cls.load_text(data['text'])
        corpus.phones = cls.load_phones(data['phones'])
        corpus.silences = cls.load_silences(data['silences'])
        corpus.utt2spk = cls.load_utt2spk(data['utt2spk'])
        corpus.variants = cls.load_variants(data['variants'])
        return corpus

    @staticmethod
    def _load_corpus_dir(corpus_dir):
        """Return path to corpus files as a dictionary

        Raise IOError if a file is not here.

        """
        corpus_dir = os.path.abspath(corpus_dir)
        data = {}

        # special case of wavs directory
        path = os.path.join(corpus_dir, 'wavs')
        if not os.path.isdir(path):
            raise IOError('invalid corpus: not found {}'.format(path))
        data['wavs'] = path

        # other are txt files
        for f in ('lexicon', 'phones', 'segments', 'silences',
                  'text', 'utt2spk', 'variants'):
            path = os.path.join(corpus_dir, f + '.txt')
            if not os.path.isfile(path):
                raise IOError('invalid corpus: not found {}'.format(path))
            data[f] = path

        return data

    @staticmethod
    def load_wavs(path):
        """Return a dict of wav files found in `path`

        `path` is assumed to be an existing directory, every files
        other than wavs are ignored.

        """
        return {os.path.splitext(os.path.basename(wav))[0]:
                os.path.realpath(wav) for wav in
                utils.list_files_with_extension(path, '.wav', abspath=True)}

    @staticmethod
    def load_lexicon(path):
        """Return a dict of word to phones entries loaded from `path`

        `path` is assumed to be a lexicon file, usually named 'lexicon.txt'

        """
        lines = (line.strip().split() for line in utils.open_utf8(path, 'r'))
        return {line[0]: ' '.join(line[1:]) for line in lines}

    @staticmethod
    def load_segments(path):
        """Return a dict of utterance ids mapped to (wav, tbegin, tend)

        `path` is assumed to be a segments file, usually named
        'segments.txt'. If there is only one utterance per wav, tbegin
        and tend are None.

        """
        def wav_tuple(l):
            p = os.path.splitext(l[0])[0]
            return ((p, None, None) if len(l) == 1
                    else (p, float(l[1]), float(l[2])))

        lines = (line.strip().split() for line in utils.open_utf8(path, 'r'))
        return {line[0]: wav_tuple(line[1:]) for line in lines}

    @staticmethod
    def load_text(path):
        """Return a dict of utterance ids mapped to their textual content

        `path` is assumed to be a text file, usually named 'text.txt'.

        """
        lines = (line.strip().split() for line in utils.open_utf8(path, 'r'))
        return {line[0]: ' '.join(line[1:]) for line in lines}

    @staticmethod
    def load_phones(path):
        """Return a dict of phones mapped to their IPA equivalent

        `path` is assumed to be a phones file, usually named 'phones.txt'.

        """
        lines = (line.strip().split() for line in utils.open_utf8(path, 'r'))
        return {line[0]: line[1] for line in lines}

    @staticmethod
    def load_silences(path):
        """Return a list of silence symbols

        `path` is assumed to be a silences file, usually named 'silences.txt'.

        """
        return [line.strip() for line in utils.open_utf8(path, 'r')]

    @classmethod
    def load_utt2spk(cls, path):
        """Return a dict of utt-ids mapped to their speaker

        `path` is assumed to be a utt2spk file, usually named 'utt2spk.txt'.

        """
        return cls.load_phones(path)

    @staticmethod
    def load_variants(path):
        """Return a list of variant symbols

        `path` is assumed to be a variants file, usually named 'variants.txt'.

        """
        return [line.strip() for line in utils.open_utf8(path, 'r')]
