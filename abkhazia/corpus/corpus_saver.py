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
"""Provides the CorpusSaver class"""

import os
import shutil
import abkhazia.utils as utils


class CorpusSaver(object):
    """Save a corpus to a directory"""
    @classmethod
    def save(cls, corpus, path, no_wavs=False):
        """Save the `corpus` to the directory `path`

        `path` is assumed to be a non existing directory.

        `corpus` is a instance of Corpus

        """
        if not os.path.exists(path):
            os.makedirs(path)

        def _path(f):
            return os.path.join(path, f)

        if not no_wavs:
            cls.save_wavs(corpus, _path('wavs'))
        cls.save_lexicon(corpus, _path('lexicon.txt'))
        cls.save_segments(corpus, _path('segments.txt'))
        cls.save_text(corpus, _path('text.txt'))
        cls.save_phones(corpus, _path('phones.txt'))
        cls.save_silences(corpus, _path('silences.txt'))
        cls.save_utt2spk(corpus, _path('utt2spk.txt'))
        cls.save_variants(corpus, _path('variants.txt'))
        corpus.meta.save(_path('meta.txt'))

    @staticmethod
    def save_wavs(corpus, path, copy_wavs=False):
        """Save the corpus wavs in `path`

        `path` is assumed to be a non existing directory

        If `copy_wavs` is True, copy the wavs in `path` else make
        symlinks

        """
        os.makedirs(path)

        func = shutil.copy if copy_wavs is True else os.symlink
        for wav in (os.path.realpath(w) for w in corpus.wavs.itervalues()):
            func(wav, os.path.join(path, os.path.basename(wav)))

    @staticmethod
    def save_lexicon(corpus, path):
        with utils.open_utf8(path, 'w') as out:
            for k, v in sorted(corpus.lexicon.iteritems()):
                out.write(u'{} {}\n'.format(k, v))

    @staticmethod
    def save_segments(corpus, path):
        with utils.open_utf8(path, 'w') as out:
            for k, v in sorted(corpus.segments.iteritems()):
                # different case with/without timestamps
                v = (v[0] if v[1] is None and v[2] is None
                     else u'{} {} {}'.format(v[0], v[1], v[2]))
                out.write(u'{} {}\n'.format(k, v))

    @staticmethod
    def save_text(corpus, path):
        with utils.open_utf8(path, 'w') as out:
            for k, v in sorted(corpus.text.iteritems()):
                out.write(u'{} {}\n'.format(k, v))

    @staticmethod
    def save_phones(corpus, path):
        with utils.open_utf8(path, 'w') as out:
            for k, v in sorted(corpus.phones.iteritems()):
                out.write(u'{} {}\n'.format(k, v))

    @staticmethod
    def save_silences(corpus, path):
        with utils.open_utf8(path, 'w') as out:
            for s in sorted(corpus.silences):
                out.write(u'{}\n'.format(s))

    @staticmethod
    def save_utt2spk(corpus, path):
        with utils.open_utf8(path, 'w') as out:
            for utt, spk in sorted(corpus.utt2spk.iteritems()):
                out.write(u'{} {}\n'.format(utt, spk))

    @staticmethod
    def save_variants(corpus, path):
        with utils.open_utf8(path, 'w') as out:
            for v in sorted(corpus.variants):
                out.write(u'{}\n'.format(v))
