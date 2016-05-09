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
"""Provides the Corpus and CorpusValidation classes"""

import collections
import os
import shutil

import abkhazia.utils as utils


class Corpus(object):
    """Usefull binding to speech corpora in the abkhazia format"""

    def __init__(self):
        """Init an empty corpus"""
        self.wavs = None
        self.lexicon = None
        self.segments = None
        self.text = None
        self.phones = None
        self.silences = None
        self.utt2spk = None
        self.variants = None

    @classmethod
    def load(cls, corpus_dir, validate=False):
        """Return a corpus initialized from `corpus_dir`

        If `validate` is True, proceed to a full data validation and
        raise IOError on the first detected error.

        Raise IOError if corpus_dir if an invalid abkhazia corpus
        directory.

        """
        # get the corpus data files as dict basename -> abspath
        data = cls._load_corpus_dir(corpus_dir)

        # init the corpus from data files
        corpus = cls()
        corpus.wavs = cls._load_wavs(data['wavs'])
        corpus.lexicon = cls._load_lexicon(data['lexicon'])
        corpus.segments = cls._load_segments(data['segments'])
        corpus.text = cls._load_text(data['text'])
        corpus.phones = cls._load_phones(data['phones'])
        corpus.silences = cls._load_silences(data['silences'])
        corpus.utt2spk = cls._load_utt2spk(data['utt2spk'])
        corpus.variants = cls._load_variants(data['variants'])

        if validate is True:
            CorpusValidation(corpus).validate()

        return corpus

    def save(self, path, copy_wavs=False):
        """Save the corpus to the directory `path`

        `path` is assumed to be a non existing directory.

        If `copy_wavs` if True, force a file copy, else use symlinks.

        """
        def _local(f):
            return os.path.join(path, f)

        os.makedirs(path)
        self._save_wavs(_local('wavs'))
        self._save_lexicon(_local('lexicon.txt'))
        self._save_segments(_local('segments.txt'))
        self._save_text(_local('text.txt'))
        self._save_phones(_local('phones.txt'))
        self._save_silences(_local('silences.txt'))
        self._save_utt2spk(_local('utt2spk.txt'))
        self._save_variants(_local('variants.txt'))

    @staticmethod
    def _load_corpus_dir(corpus_dir):
        """Return path to corpus files as a dictionary

        Raise IOError if a file is not here.

        """
        corpus_dir = os.path.abspath(corpus_dir)
        data = {}

        # special case of wavs dircetory
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
    def _load_wavs(path):
        """Return a dict of wav files found in `path`

        `path` is assumed to be an existing directory, every files
        other than wavs are ignored.

        """
        return dict((os.path.splitext(os.path.basename(wav))[0], wav)
                    for wav in utils.list_files_with_extension(
                            path, '.wav', abspath=True))

    @staticmethod
    def _load_lexicon(path):
        """Return a dict of word to phones entries loaded from `path`

        `path` is assumed to be a lexicon file, usually named 'lexicon.txt'

        """
        lines = (line.strip().split() for line in utils.open_utf8(path, 'r'))
        return dict((line[0], ' '.join(line[1:])) for line in lines)

    @staticmethod
    def _load_segments(path):
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
        return dict((line[0], wav_tuple(line[1:])) for line in lines)

    @staticmethod
    def _load_text(path):
        """Return a dict of utterance ids mapped to their textual content

        `path` is assumed to be a text file, usually named 'text.txt'.

        """
        lines = (line.strip().split() for line in utils.open_utf8(path, 'r'))
        return dict((line[0], ' '.join(line[1:])) for line in lines)

    @staticmethod
    def _load_phones(path):
        """Return a dict of phones mapped to their IPA equivalent

        `path` is assumed to be a phones file, usually named 'phones.txt'.

        """
        lines = (line.strip().split() for line in utils.open_utf8(path, 'r'))
        return dict((line[0], line[1]) for line in lines)

    @staticmethod
    def _load_silences(path):
        """Return a list of silence symbols

        `path` is assumed to be a silences file, usually named 'silences.txt'.

        """
        return [line.strip() for line in utils.open_utf8(path, 'r')]

    @classmethod
    def _load_utt2spk(cls, path):
        """Return a dict of utt-ids mapped to their speaker

        `path` is assumed to be a utt2spk file, usually named 'utt2spk.txt'.

        """
        return cls._load_phones(path)

    @staticmethod
    def _load_variants(path):
        """Return a list of variant symbols

        `path` is assumed to be a variants file, usually named 'variants.txt'.

        """
        return [line.strip() for line in utils.open_utf8(path, 'r')]

    def _save_wavs(self, path, copy_wavs=False):
        os.makedirs(path)

        for w in self.wavs.itervalues():
            target = os.path.join(path, os.path.basename(w))
            # if copy_wavs is True:
            #     shutil.copy(w, target)
            # else:
            os.symlink(w, target)

    def _save_lexicon(self, path):
        with utils.open_utf8(path, 'w') as out:
            for k, v in self.lexicon.iteritems():
                out.write('{} {}\n'.format(k, v))

    def _save_segments(self, path):
        with utils.open_utf8(path, 'w') as out:
            for k, v in self.segments.iteritems():
                # different case with/without timestamps
                v = (v[0] if v[1] is None and v[2] is None
                     else '{} {} {}'.format(v[0], v[1], v[2]))
                out.write('{} {}\n'.format(k, v))

    def _save_text(self, path):
        with utils.open_utf8(path, 'w') as out:
            for k, v in self.text.iteritems():
                out.write('{} {}\n'.format(k, v))

    def _save_phones(self, path):
        with utils.open_utf8(path, 'w') as out:
            for k, v in self.phones.iteritems():
                out.write(u'{} {}\n'.format(k, v))

    def _save_silences(self, path):
        with utils.open_utf8(path, 'w') as out:
            for s in self.silences:
                out.write('{}\n'.format(s))

    def _save_utt2spk(self, path):
        with utils.open_utf8(path, 'w') as out:
            for k, v in self.utt2spk.iteritems():
                out.write('{} {}\n'.format(k, v))

    def _save_variants(self, path):
        with utils.open_utf8(path, 'w') as out:
            for v in self.variants:
                out.write('{}\n'.format(v))


class CorpusValidation(object):
    """Checks a given speech corpus is in a valid state

    corpus (Corpus): the abkhazia corpus to validate.

    njobs (int): number of jobs for parallel processing (default is
      number of cores on the machine).

    log (logging.Logger): the logging instance to send messages, by
      default disable logging.

    Beware that it automatically corrects some basics problems and
    thus it can modify the original corpus. For example it add default
    values to phone inventories when they are missing.

    Methods
    -------

    The one call solution to validate the corpus is to call
    validate(). If you want a fine-grained validation, use the
    specialized validate_SOMETHING() methods.

    """
    def __init__(self, corpus, njobs=utils.default_njobs(),
                 log=utils.log2file.null_logger()):
        self.njobs = njobs
        self.log = log
        self.corpus = corpus

    def validate(self, meta=None):
        """Validate the whole corpus

        Log information about the corpus. Raise an IOError on the
        first detected error. If the function returns without raising,
        this means the corpus is compatible with abkhazia.

        Return metainformation on the wavs (from utils.wav.scan)

        If meta is not None, it is assumed that it comes from a
        previous call to validate(). This trick is used during
        validation of splited corpora, which share the same wavs
        collection.

        """
        self.log.info('validating abkhazia corpus')

        if meta is None:
            meta = self.validate_wavs()

        self.validate_segments(meta)
        self.validate_speakers()
        self.validate_transcription()

        inventory = self.validate_phones()
        # self.validate_lexicon(inventory)

        self.log.info("corpus validated: ready for use with abkhazia")
        return meta

    def validate_wavs(self):
        """Corpus wavs must be mono 16KHz, 16 bit PCM"""
        self.log.debug("checking wavs")
        wavs = self.corpus.wavs

        wrong_extensions = [
            w for w in wavs.values() if os.path.splitext(w)[1] != ".wav"]

        if wrong_extensions:
            raise IOError(
                "The following wavs do not have a '.wav' extension: {}"
                .format(wrong_extensions))

        # get meta information on the wavs
        meta = utils.wav.scan(wavs.values(), njobs=self.njobs)
        meta = dict((os.path.splitext(os.path.basename(k))[0], v)
                    for k, v in meta.iteritems())

        empty_files = [w for w in wavs.keys() if meta[w].nframes == 0]
        if empty_files:
            raise IOError("The following files are empty: {}"
                          .format(empty_files))

        weird_rates = [w for w in wavs.keys() if meta[w].rate != 16000]
        if weird_rates:
            raise IOError(
                "Currently only files sampled at 16,000 Hz "
                "are supported. The following files are sampled "
                "at other frequencies: {0}".format(weird_rates))

        non_mono = [w for w in wavs.keys() if meta[w].nbc != 1]
        if non_mono:
            raise IOError(
                "Currently only mono files are supported. "
                "The following files have more than "
                "one channel: {0}".format(non_mono))

        # in bytes: 16 bit == 2 bytes
        non_16bit = [w for w in wavs.keys() if meta[w].width != 2]
        if non_16bit:
            raise IOError(
                "Currently only files encoded on 16 bits are "
                "supported. The following files are not encoded "
                "in this format: {0}"
                .format(non_16bit))

        compressed = [w for w in wavs.keys() if meta[w].comptype != 'NONE']
        if compressed:
            raise IOError(
                "The following files are compressed: {0}"
                .format(compressed))

        self.log.debug("'wavs' folder is OK")
        return meta

    def validate_segments(self, meta):
        """Checking utterances list in segments"""
        self.log.debug("Checking utterances in segments")
        segments = self.corpus.segments
        utt_ids = segments.keys()
        utt_wavs = [w[0] for w in segments.itervalues()]
        starts = [w[1] for w in segments.itervalues()]
        stops = [w[2] for w in segments.itervalues()]

        # unique utterance-ids
        duplicates = utils.duplicates(utt_ids)
        if duplicates:
            raise IOError(
                "There is utterance-ids in "
                "'segments.txt' used several times: {0}"
                .format(duplicates))

        # all referenced wavs are in wav folder
        missing_wavefiles = set.difference(
            set(utt_wavs), set(self.corpus.wavs.keys()))
        if missing_wavefiles:
            raise IOError(
                "The following wavefiles are referenced "
                "in segments but are not in wavs"
                .format(missing_wavefiles))

        if(len(set(utt_wavs)) == len(utt_wavs) and
           all([e is None for e in starts]) and
           all([e is None for e in stops])):
            # simple case, with one utterance per file and no explicit
            # timestamps provided just get list of files that are very
            # short (less than 15ms)
            short_wavs = [utt_id for utt_id, wav in zip(utt_ids, utt_wavs)
                          if meta[wav].duration < .015]
        else:
            # more complicated case :find all utterances (plus
            # timestamps) associated to each wavefile and for each
            # wavefile, check consistency of the timestamps of all
            # utterances inside it
            warning, short_wavs = self._check_timestamps(
                meta, utt_ids, utt_wavs, starts, stops)
            if warning:
                self.log.warning(
                    "Some utterances are overlapping in time, "
                    "see details in log file:\n{}".format(self.log_file))

        if short_wavs:
            self.log.debug(
                "The following utterances are less than 15ms long and "
                "won't be used in kaldi recipes: {}".format(short_wavs))

        self.log.debug("segments are OK")

    def validate_speakers(self):
        """Checking speakers from corpus.utt2spk"""
        self.log.debug("checking speakers")

        utt_ids_spk = self.corpus.utt2spk.keys()
        speakers = self.corpus.utt2spk.values()
        utt_ids = self.corpus.segments.keys()

        # same utterance-ids in segments.txt and utt2spk.txt
        if utt_ids_spk != utt_ids:
            duplicates = utils.duplicates(utt_ids_spk)
            if duplicates:
                raise IOError(
                    "The following utterance-ids are used several times "
                    "in 'utt2spk.txt': {}".format(duplicates))
            else:
                e_spk = set(utt_ids_spk)
                e_seg = set(utt_ids)

                self.log.debug(
                    "Utterances in utt2spk.txt that are not in "
                    "segments.txt: {}".format(set.difference(e_spk, e_seg)))

                self.log.debug(
                    "Utterances in segments.txt that are not in "
                    "utt2spk.txt: {}".format(set.difference(e_seg, e_spk)))

                raise IOError(
                    "Utterance-ids in 'segments.txt' and 'utt2spk.txt' are "
                    "not consistent, see details in log:\n{}"
                    .format(self.log_file))

        # speaker ids must have a fixed length
        default_len = len(speakers[0])
        if not all([len(s) == default_len for s in speakers]):
            self.log.debug(
                "Speaker-ids length observed in utt2spk.txt with associated "
                "frequencies: {0}".format(
                    collections.Counter([len(s) for s in speakers])))

            raise IOError(
                "All speaker-ids must have the same length. "
                "See log for more details:\n{}".format(self.log_file))

        # each speaker id must be prefix of corresponding utterance-id
        for utt, spk in zip(utt_ids, speakers):
            if not utt[:default_len] == spk:
                raise IOError(
                    "All utterance-ids must be prefixed by the "
                    "corresponding speaker-id")

        self.log.debug("speakers are OK")

    def validate_transcription(self):
        """Checking transcriptions"""
        self.log.debug("checking transcriptions")

        utt_ids = self.corpus.segments.keys()
        utt_ids_txt = self.corpus.text.keys()

        # we will check that the words are mostly in the lexicon later
        # same utterance-ids in segments.txt and text.txt
        if utt_ids_txt != utt_ids:
            duplicates = utils.duplicates(utt_ids_txt)
            if duplicates:
                self.log.debug(
                    "There is several utterance-ids used several times "
                    "in text: {}".format(len(duplicates)))

                raise IOError(
                    "There is several utterance-ids used several times "
                    "in text: {}".format(duplicates))
            else:
                e_txt = set(utt_ids_txt)
                e_seg = set(utt_ids)

                self.log.debug(
                    "Utterances in text that are not in segments.txt: {}"
                    .format(set.difference(e_txt, e_seg)))

                self.log.debug(
                    "Utterances in segments that are not in text.txt: {}"
                    .format(set.difference(e_seg, e_txt)))

                raise IOError(
                    "Utterance-ids in segments and text are "
                    "not consistent, see details in log:\n{}"
                    .format(self.log_file))

        self.log.debug("text is OK")

    def validate_phones(self):
        """Checks phones, silences and variants, return phones inventory"""
        phones = self._check_phones()
        sils = self._check_silences(phones)
        return self._check_variants(phones, sils)

    def _check_phones(self):
        # TODO check xsampa compatibility and/or compatibility
        # with articulatory features databases of IPA or just basic
        # IPA correctness
        self.log.debug('checking phones')
        phones = self.corpus.phones.keys()
        ipas = self.corpus.phones.values()

        if u'SIL' in phones:
            raise IOError(
                "'SIL' symbol is reserved for indicating "
                "optional silence, it cannot be used in phones")

        if u'SPN' in phones:
            raise IOError(
                "'SPN' symbol is reserved for indicating "
                "vocal noise, it cannot be used in phones")

        duplicates = utils.duplicates(phones)
        if duplicates:
            raise IOError(
                "The following phone symbols are used several times "
                "in phones: {}".format(duplicates))

        duplicates = utils.duplicates(ipas)
        if duplicates:
            raise IOError(
                "The following IPA symbols are used several times "
                "in phones: {}".format(duplicates))

        return phones

    def _check_silences(self, phones):
        self.log.debug('checking silences')

        sils = self.corpus.silences
        if len(sils) == 0:
            self.log.warning(
                "No silence symbols, adding 'SIL' and 'SPN'")
            sils += ['SIL', 'SPN']
        else:
            duplicates = utils.duplicates(sils)
            if duplicates:
                raise IOError(
                    "The following symbols are used several times "
                    "in 'silences.txt': {}".format(duplicates))

            if u"SIL" not in sils:
                self.log.debug("Adding missing 'SIL' symbol to silences")
                sils.append('SIL')

            if u"SPN" not in sils:
                self.log.debug("Adding missing 'SPN' symbol to silences")
                sils.append('SPN')

            inter = set.intersection(set(sils), set(phones))
            if inter:
                raise IOError(
                    "The following symbols are used in both phones "
                    "and silences: {}".format(inter))

            return sils

    def _check_variants(self, phones, sils):
        self.log.debug('checking phones variants')

        variants = self.corpus.variants

        all_symbols = [symbol for group in variants for symbol in group]
        unknown_symbols = [symbol for symbol in all_symbols
                           if symbol not in phones and symbol not in sils]
        if unknown_symbols:
            raise IOError(
                "The following symbols are present in variants, "
                "but are neither in phones nor in silences: "
                "{}".format(unknown_symbols))

            duplicates = utils.duplicates(all_symbols)
            if duplicates:
                raise IOError(
                    "The following symbols are used several times "
                    "in variants: {}".format(duplicates))

        self.log.debug("phones inventory is OK")
        inventory = set.union(set(phones), set(sils))
        return inventory

    def validate_lexicon(self, inventory):
        self.log.debug("Checking lexicon")

        dict_words = self.corpus.lexicon.keys()
        transcriptions = self.corpus.lexicon.values()

        # unique word entries (alternative pronunciations are not
        # currently supported)
        duplicates = utils.duplicates(dict_words)
        if duplicates:
            raise IOError(
                "Alternative pronunciations are not currently supported. "
                "The following words have several transcriptions "
                "in 'lexicon.txt': {0}".format(duplicates))

        # OOV item
        if u"<unk>" not in dict_words:
            self.log.debug("No '<unk>' word in lexicon, adding one")
            dict_words.append(u"<unk>")
            transcriptions.append([u"SPN"])
        else:
            if transcriptions[dict_words.index(u"<unk>")] != [u"SPN"]:
                raise IOError(
                    "'<unk>' word is reserved for mapping "
                    "OOV items and should always be transcribed "
                    "as 'SPN' (vocal) noise'")
        # Should we log a warning for all words containing silence phones?

        # unused words
        utt_words = (word for utt in self.corpus.text.itervalues()
                     for word in utt.split())
        dict_words_set = set(dict_words)
        used_words = [word for words in utt_words for word in words]
        used_word_types = set(used_words)
        used_word_counts = collections.Counter(used_words)
        used_dict_words = set.intersection(dict_words_set, used_word_types)
        self.log.debug("{} dictionary words used out of {}"
                       .format(len(used_dict_words), len(dict_words_set)))

        # oov words
        oov_word_types = set.difference(used_word_types, dict_words_set)
        oov_word_counts = collections.Counter(
            {oov: used_word_counts[oov] for oov in oov_word_types})
        nb_oov_tokens = sum(oov_word_counts.values())
        nb_oov_types = len(oov_word_types)

        self.log.debug(
            u"{} OOV word types in transcriptions out of {} types in total"
            .format(nb_oov_types, len(used_word_types)))

        self.log.debug(
            u"{} OOV word tokens in transcriptions out of {} tokens in total"
            .format(nb_oov_tokens, len(used_words)))

        self.log.debug(
            u"List of OOV word types with occurences counts: {0}"
            .format(self._strcounts2unicode(oov_word_counts.most_common())))

        # raise alarm if the proportion of oov words is too large
        # either in terms of types or tokens
        oov_proportion_types = nb_oov_types/float(len(used_word_types))
        oov_proportion_tokens = nb_oov_tokens/float(len(used_words))
        self.log.debug("Proportion of oov word types: {}"
                       .format(oov_proportion_types))

        self.log.debug("Proportion of oov word tokens: {}"
                       .format(oov_proportion_tokens))

        if oov_proportion_types > 0.1:
            self.log.warning('More than 10 percent of word '
                             'types used are Out-Of-Vocabulary items!')

        if oov_proportion_tokens > 0.1:
            self.log.warning('More than 10 percent of word '
                             'tokens used are Out-Of-Vocabulary items!')

        # homophones (issue warnings only)
        counts = collections.Counter(
            [u" ".join(phone_trans) for phone_trans in transcriptions])

        duplicate_transcripts = collections.Counter(
            {trans: counts[trans] for trans in counts if counts[trans] > 1})

        if duplicate_transcripts:
            self.log.warning(
                u"There are homophones in the pronunciation dictionary, "
                u"see log for details:\n{}".format(self.log_file))

            self.log.debug(
                u'There are {} phone sequences that correspond to several '
                u'words in the pronunciation dictionary'
                .format(len(duplicate_transcripts)))

            self.log.debug(
                'There are {} word types with homophones in the pronunciation '
                'dictionary'.format(sum(duplicate_transcripts.values())))

            self.log.debug(
                "List of homophonic phone sequences in 'lexicon.txt' "
                "with number of corresponding word types: {0}"
                .format(self._strcounts2unicode(
                    duplicate_transcripts.most_common())))

            # Commented because it takes a lot of times for certain corpora
            # Maybe put it as an option
            # # get word types:
            # #    - found in transcriptions
            # #    - with at least one homophonic word type also found in transcriptions
            # homophonic_sequences = duplicate_transcripts.keys()
            # homophony_groups = {}
            # for homo_transcript in homophonic_sequences:
            #     homo_group = [word for word, transcript in zip(dict_words, str_transcripts) \
            #                 if transcript == homo_transcript and word in used_word_types]
            #     if len(homo_group) > 1:
            #         homophony_groups[homo_transcript] = homo_group
            # nb_homo_types = sum([len(homo_group) for homo_group in homophony_groups.values()])
            # log.warning(
            #     (
            #     u"{0} word types found in transcriptions with "
            #     u"at least one homophone also found in transcriptions "
            #     u"out of {1} word types in total"
            #     ).format(nb_homo_types, len(used_word_types))
            # )
            # nb_homo_tokens = sum([sum([used_word_counts[word] for word in homo_group]) for homo_group in homophony_groups.values()])
            # log.warning((u"{0} corresponding word tokens out of {1} total").format(nb_homo_tokens, len(used_words)))
            # l = [", ".join([word + u": " + unicode(used_word_counts[word]) for word in group]) for group in homophony_groups.values()]
            # s = "\n".join(l)
            # log.warning(
            #     (
            #     u"List of groups of homophonic word types "
            #     u"(including only types actually found in transcriptions) "
            #     u"with number of occurences of each member of each group:\n{0}"
            #     ).format(s)
            # )

        # ooi phones
        used_phones = [phone for trans_phones in transcriptions
                       for phone in trans_phones]

        ooi_phones = [phone for phone in set(used_phones)
                      if phone not in inventory]

        if ooi_phones:
            raise IOError(
                u"Phonetic dictionary uses out-of-inventory phones: {0}"
                .format(ooi_phones))

        # warning for unused phones
        unused_phones = set.difference(inventory, used_phones)
        if unused_phones:
            self.log.debug(
                "The following phones are never found "
                "in the transcriptions: {}".format(unused_phones))

        self.log.debug('lexicon is OK')

    def _check_timestamps(self, meta, utt_ids, utt_wavs, starts, stops):
        '''Check for utterances overlap and timestamps consistency'''
        self.log.debug("checking timestamps consistency...")

        short_wavs = []
        warning = False
        for wav in utt_wavs:
            duration = meta[wav].duration
            utts = [(utt,
                     0 if sta is None else sta,
                     duration if sto is None else sto)
                    for utt, w, sta, sto
                    in zip(utt_ids, self.corpus.wavs.keys(), starts, stops)
                    if w == wav]

            # first check that start < stop and within file duration
            for utt_id, start, stop in utts:
                if not stop >= start:  # should it be > ?
                    raise IOError(
                        "Stop time for utterance {0} is lower than "
                        "start time".format(utt_id))

                if not 0 <= start <= duration:
                    raise IOError(
                        "Start time for utterance {} is not compatible "
                        "with file duration in {}: {} -> {}"
                        .format(utt_id, wav, start, duration))

                if not 0 <= stop <= duration:
                    raise IOError(  # print(
                        "Stop time for utterance {} is not compatible "
                        "with file duration in {}: {} > {}"
                        .format(utt_id, wav, stop, duration))

                if stop - start < .015:
                    short_wavs.append(utt_id)

            # then check if there is overlap in time between the
            # different utterances and if there is, issue a
            # warning (not an error)

            # 1. check that no two utterances start or finish at
            # the same time
            wav_starts = [start for _, start, _ in utts]
            counts = collections.Counter(wav_starts)
            same_start = {}
            for start in counts:
                if counts[start] > 1:
                    same_start[start] = [utt for utt, sta, _ in utts
                                         if sta == start]

            wav_stops = [stop for _, _, stop in utts]
            counts = collections.Counter(wav_stops)
            same_stop = {}
            for stop in counts:
                if counts[stop] > 1:
                    same_stop[stop] = [utt for utt, _, sto in utts
                                       if sto == stop]

            if same_start:
                warning = True
                self.log.warning(
                    "The following utterances start at the same time "
                    "in wavefile {}: {}".format(wav, same_start))

            if same_stop:
                warning = True
                self.log.warning(
                    "The following utterances stop at the same time "
                    "in wavefile {0}: {1}".format(wav, same_stop))

            # 2. now it suffices to check the following:
            timestamps = list(set(wav_starts)) + list(set(wav_stops))
            timestamps.sort()

            # TODO fix that... maybe > 1
            overlapped = [
                (utt, timestamps.index(stop) - timestamps.index(start))
                for utt, start, stop in utts
                if timestamps.index(stop) - timestamps.index(start) != 1]

            if overlapped:
                warning = True
                self.log.warning(
                    "The following utterances from file {} are "
                    "overlapping in time: {}".format(wav, overlapped))

            return warning, short_wavs
