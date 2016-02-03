# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 00:17:47 2015

@author: Thomas Schatz
"""

"""
This script checks whether a given speech corpus is correctly formatted
for usage with abkhazia tools.

Beware that it automatically corrects some basics problems and thus it can
modify the original files. For example it sorts the lines of some text files
and add default values to phone inventories when they are missing.
"""
# TODO: optimize homophone processing for large dictionaries

import argparse
import codecs
import collections
import contextlib
import os
import wave

import abkhazia.utilities.log2file as log2file
import abkhazia.utilities.basic_io as io


def with_default(value, default):
    return default if value is None else value


def get_duplicates(iterable):
    """Return a list of duplicates elements in iterable"""
    counts = collections.Counter(iterable)
    duplicates = [e for e in counts if counts[e] > 1]
    return duplicates


def strcounts2unicode(strcounts):
    return u", ".join([u"'" + s + u"': " + unicode(c) for s, c in strcounts])


def validate(corpus_path, verbose=False):
    """Check corpus directory structure and set log files up"""
    data_dir = os.path.join(corpus_path, 'data')
    if not(os.path.isdir(data_dir)):
        raise IOError("Corpus folder {0} should contain a 'data' subfolder".format(corpus_path))
    log_dir = os.path.join(corpus_path, 'logs')
    if not(os.path.isdir(log_dir)):
            os.mkdir(os.path.join(corpus_path, "logs"))

    # log file config
    log_file = os.path.join(log_dir, "data_validation.log".format(corpus_path))
    log = log2file.get_log(log_file, verbose)

    try:
        """
        wav directory must contain only mono wavefiles in 16KHz, 16 bit PCM format
        """
        log.debug("Checking 'wavs' folder")
        wav_dir = os.path.join(data_dir, 'wavs')
        wavefiles = [e for e in os.listdir(wav_dir) if e != '.DS_Store']
        durations = {}
        wrong_extensions = [f for f in wavefiles if f[-4:] != ".wav"]
        if wrong_extensions:
            raise IOError(
                (
                "The following files in 'wavs' folder do "
                "not have a '.wav' extension: {0}"
                ).format(wrong_extensions)
            )
        nb_channels, width, rate, nframes, comptype, compname = {}, {}, {}, {}, {}, {}
        for f in wavefiles:
            filepath = os.path.join(wav_dir, f)
            with contextlib.closing(wave.open(filepath,'r')) as fh:
                (nb_channels[f], width[f], rate[f],
                 nframes[f], comptype[f], compname[f]) = fh.getparams()
                durations[f] = nframes[f]/float(rate[f])
        empty_files = [f for f in wavefiles if nframes[f] == 0]
        if empty_files:
            raise IOError("The following files are empty: {0}".format(empty_files))
        weird_rates = [f for f in wavefiles if rate[f] != 16000]
        if weird_rates:
            raise IOError(
                (
                "Currently only files sampled at 16,000 Hz "
                "are supported. The following files are sampled "
                "at other frequencies: {0}"
                ).format(weird_rates)
            )
        non_mono = [f for f in wavefiles if nb_channels[f] != 1]
        if non_mono:
            raise IOError(
                (
                "Currently only mono files are supported. "
                "The following files have more than "
                "one channel: {0}"
                ).format(non_mono)
            )
        non_16bit = [f for f in wavefiles if width[f] != 2]  # in bytes: 16 bit == 2 bytes
        if non_16bit:
            raise IOError(
                (
                "Currently only files encoded on 16 bits are "
                "supported. The following files are not encoded "
                "in this format: {0}"
                ).format(non_16bit)
            )
        compressed = [f for f in wavefiles if comptype[f] != 'NONE']
        if compressed:
            raise IOError("The following files are compressed: {0}".format(compressed))
        log.debug("'wavs' folder is OK")


        """
        checking utterances list
        """
        log.debug("Checking 'segments.txt' file")
        log.debug("C++ sort file")
        seg_file = os.path.join(data_dir, "segments.txt")
        io.cpp_sort(seg_file)  # C++ sort file for convenience
        utt_ids, wavs, starts, stops = io.read_segments(seg_file)
        # unique utterance-ids
        duplicates = get_duplicates(utt_ids)
        if duplicates:
            raise IOError(
                (
                "The following utterance-ids in "
                "'segments.txt' are used several times: {0}"
                ).format(duplicates)
            )
        # all referenced wavs are in wav folder
        missing_wavefiles = set.difference(set(wavs), set(wavefiles))
        if missing_wavefiles:
            raise IOError(
                (
                "The following wavefiles are referenced "
                "in 'segments.txt' but are not in wav folder: {0}"
                ).format(missing_wavefiles)
            )
        if len(set(wavs)) == len(wavs) \
        and all([e is None for e in starts]) \
        and all([e is None for e in stops]):
            # simple case, with one utterance per file and no explicit timestamps provided
            # just get list of files that are very short (less than 15ms)
            short_wavs = [utt_id for utt_id, wav in zip(utt_ids, wavs) if durations[wav] < .015]
        else:
            # more complicated case
            # find all utterances (plus timestamps) associated to each wavefile
            # and for each wavefile, check consistency of the timestamps of
            # all utterances inside it
            # report progress as this can be a bit long
            n = len(wavefiles)
            next_display_prop = 0.1
            log.debug("Checked timestamps consistency for 0% of wavefiles")
            warning = True
            short_wavs = []
            for i, wav in enumerate(wavefiles):
                duration = durations[wav]
                utts = [(utt, with_default(sta, 0), with_default(sto, duration)) for utt, w, sta, sto in zip(utt_ids, wavs, starts, stops) if w == wav]
                # first check that start < stop and within file duration
                for utt_id, start, stop in utts:
                    assert stop >= start, \
                        "Stop time for utterance {0} is lower than start time".format(utt_id)  # should it be >?
                    assert 0 <= start <= duration, \
                        "Start time for utterance {0} is not compatible with file duration".format(utt_id)
                    assert 0 <= stop <= duration, \
                        "Stop time for utterance {0} is not compatible with file duration".format(utt_id)
                    if stop-start < .015:
                        short_wavs.append(utt_id)
                # then check if there is overlap in time between the different utterances
                # and if there is, issue a warning (not an error)
                # 1. check that no two utterances start or finish at the same time
                wav_starts = [start for _, start, _ in utts]
                counts = collections.Counter(wav_starts)
                same_start = {}
                for start in counts:
                    if counts[start] > 1:
                        same_start[start] = [utt for utt, sta, _ in utts if sta == start]
                wav_stops = [stop for _, _, stop in utts]
                counts = collections.Counter(wav_stops)
                same_stop = {}
                for stop in counts:
                    if counts[stop] > 1:
                        same_stop[stop] = [utt for utt, _, sto in utts if sto == stop]
                if same_start:
                    warning = True
                    log.warning(
                        (
                        "The following utterances start at the same time "
                        "in wavefile {0}: {1}"
                        ).format(wav, same_start)
                    )
                if same_stop:
                    warning = True
                    log.warning(
                        (
                        "The following utterances stop at the same time "
                        "in wavefile {0}: {1}"
                        ).format(wav, same_stop)
                    )
                # 2. now it suffices to check the following:
                wav_starts = list(set(wav_starts))
                wav_stops = list(set(wav_stops))
                timestamps = wav_starts + wav_stops
                timestamps.sort()
                # TODO fix that... maybe > 1
                index = timestamps.index
                overlapped = [utt for utt, start, stop in utts if index(stop)-index(start) != 1]
                if overlapped:
                    warning = True
                    log.warning(
                        (
                        "The following utterances from file {0} are "
                        "overlapping in time: {1}"
                        ).format(wav, overlapped)
                    )
                # report progress as the for loop can be a bit long
                prop = (i+1)/float(n)
                if prop >= next_display_prop:
                    log.debug(
                        (
                        "Checked timestamps consistency for "
                        "{0}% of wavefiles"
                        ).format(int(round(100*next_display_prop)))
                    )
                    next_display_prop = next_display_prop + 0.1
            if warning:
                log.info(
                    (
                    "Some utterances are overlapping in time, "
                    "see details in log file {0}"
                    ).format(log_file)
                )
        if short_wavs:
            log.warning(
                (
                "The following utterances are less than 15ms long and "
                "won't be used in kaldi recipes: {0}"
                ).format(short_wavs)
            )
        log.debug("'segments.txt' file is OK")


        """
        checking speakers list
        """
        log.debug("Checking 'speakers' file")
        log.debug("C++ sort file")
        spk_file = os.path.join(data_dir, "utt2spk.txt")
        io.cpp_sort(spk_file)  # C++ sort file for convenience
        utt_ids_spk, speakers = io.read_utt2spk(spk_file)
        # same utterance-ids in segments.txt and utt2spk.txt
        if not(utt_ids_spk == utt_ids):
            duplicates = get_duplicates(utt_ids_spk)
            if duplicates:
                raise IOError(
                    (
                    "The following utterance-ids "
                    "are used several times in 'utt2spk.txt': {0}"
                    ).format(duplicates)
                )
            else:
                e_spk = set(utt_ids_spk)
                e_seg = set(utt_ids)
                e = set.difference(e_spk, e_seg)
                log.error("Utterances in utt2spk.txt that are not in segments.txt: {0}".format(e))
                e = set.difference(e_seg, e_spk)
                log.error("Utterances in segments.txt that are not in utt2spk.txt: {0}".format(e))
                raise IOError(
                    (
                    "Utterance-ids in 'segments.txt' and 'utt2spk.txt' are not consistent, "
                    "see details in log {0}"
                    ).format(log_file)
                )
        # speaker ids must have a fixed length
        l = len(speakers[0])
        if not(all([len(s) == l for s in speakers])):
            spk_len = collections.Counter([len(s) for s in speakers])
            log.error("Speaker-ids length observed in utt2spk.txt with associated frequencies: {0}".format(spk_len))
            raise IOError("All speaker-ids must have the same length. See log for more details.")

        # each speaker id must be prefix of corresponding utterance-id
        for utt, spk in zip(utt_ids, speakers):
            assert utt[:l] == spk, "All utterance-ids must be prefixed by the corresponding speaker-id"
        log.debug("'speakers' file is OK")


        """
        checking transcriptions
        """
        log.debug("Checking 'text.txt' file")
        log.debug("C++ sort file")
        txt_file = os.path.join(data_dir, "text.txt")
        io.cpp_sort(txt_file)  # C++ sort file for convenience
        utt_ids_txt, utt_words = io.read_text(txt_file)
        # we will check that the words are mostly in the lexicon later
        # same utterance-ids in segments.txt and text.txt
        if not(utt_ids_txt == utt_ids):
            duplicates = get_duplicates(utt_ids_txt)
            if duplicates:
                raise IOError(
                    (
                    "The following utterance-ids "
                    "are used several times in 'text.txt': {0}"
                    ).format(duplicates)
                )
            else:
                e_txt = set(utt_ids_txt)
                e_seg = set(utt_ids)
                e = set.difference(e_txt, e_seg)
                log.error("Utterances in text.txt that are not in segments.txt: {0}".format(e))
                e = set.difference(e_seg, e_txt)
                log.error("Utterances in segments.txt that are not in text.txt: {0}".format(e))
                raise IOError(
                    (
                    "Utterance-ids in 'segments.txt' and 'text.txt' are not consistent, "
                    "see details in log {0}"
                    ).format(log_file)
                )
        log.debug("'text.txt' file is OK, checking for OOV items later")


        """
        checking phone inventory
        """
        log.debug(
            (
            "Checking phone inventory files 'phones.txt', 'silences.txt' and "
            "'variants.txt'"
            )
        )
        # phones
        #TODO: check xsampa compatibility and/or compatibility with articulatory features databases of IPA
        # or just basic IPA correctness
        phon_file = os.path.join(data_dir, "phones.txt")
        phones, ipas = io.read_phones(phon_file)
        assert not(u"SIL" in phones), \
            (
            u"'SIL' symbol is reserved for indicating "
            u"optional silence, it cannot be used "
            u"in 'phones.txt'"
            )
        assert not(u"SPN" in phones), \
            (
            u"'SPN' symbol is reserved for indicating "
            u"vocal noise, it cannot be used "
            u"in 'phones.txt'"
            )
        duplicates = get_duplicates(phones)
        assert not(duplicates), \
            (
            u"The following phone symbols are used several times "
            u"in 'phones.txt': {0}"
            ).format(duplicates)
        duplicates = get_duplicates(ipas)
        assert not(duplicates), \
            (
            u"The following IPA symbols are used several times "
            u"in 'phones.txt': {0}"
            ).format(duplicates)
        # silences
        sil_file = os.path.join(data_dir, "silences.txt")
        if not(os.path.exists(sil_file)):
            log.warning(u"No silences.txt file, creating default one with 'SIL' and 'SPN'")
            with codecs.open(sil_file, mode='w', encoding="UTF-8") as out:
                out.write(u"SIL\n")
                out.write(u"SPN\n")
            sils = [u"SIL", u"SPN"]
        else:
            sils = io.read_silences(sil_file)
            duplicates = get_duplicates(sils)
            assert not(duplicates), \
                (
                u"The following symbols are used several times "
                u"in 'silences.txt': {0}"
                ).format(duplicates)
            if not u"SIL" in sils:
                log.warning(u"Adding missing 'SIL' symbol to silences.txt")
                with codecs.open(sil_file, mode='a', encoding="UTF-8") as out:
                    out.write(u"SIL\n")
                sils.append(u"SIL")
            if not u"SPN" in sils:
                log.warning(u"Adding missing 'SPN' symbol to silences.txt")
                with codecs.open(sil_file, mode='a', encoding="UTF-8") as out:
                    out.write(u"SPN\n")
                sils.append(u"SPN")
            inter = set.intersection(set(sils), set(phones))
            assert not(inter), \
                (
                u"The following symbols are used in both 'phones.txt' "
                u"and 'silences.txt': {0}"
                ).format(inter)
        # variants
        var_file = os.path.join(data_dir, "variants.txt")
        if not(os.path.exists(var_file)):
            log.warning(u"No variants.txt file, creating empty one")
            with codecs.open(var_file, mode='w', encoding="UTF-8") as out:
                pass
            variants = []
        else:
            variants = io.read_variants(var_file)
            all_symbols = [symbol for group in variants for symbol in group]
            unknown_symbols = [symbol for symbol in all_symbols if not(symbol in phones) and not(symbol in sils)]
            assert not(unknown_symbols), \
                (
                u"The following symbols are present "
                u"in 'variants.txt', but are "
                u"neither in 'phones.txt' nor in "
                u"'silences.txt': {0}"
                ).format(unknown_symbols)
            duplicates = get_duplicates(all_symbols)
            assert not(duplicates), \
                (
                u"The following symbols are used several times "
                u"in 'variants.txt': {0}"
                ).format(duplicates)
        inventory = set.union(set(phones), set(sils))
        log.debug("Phone inventory files are OK")


        """
        checking phonetic dictionary
        """
        log.debug("Checking 'lexicon.txt' file")
        dict_file = os.path.join(data_dir, "lexicon.txt")
        dict_words, transcriptions = io.read_dictionary(dict_file)
        # unique word entries (alternative pronunciations are not currently supported)
        duplicates = get_duplicates(dict_words)
        assert not(duplicates), \
            (
            u"Alternative pronunciations are not currently supported. "
            u"The following words have several transcriptions "
            u"in 'lexicon.txt': {0}"
            ).format(duplicates)
        # OOV item
        if not(u"<unk>" in dict_words):
            log.warning("No '<unk>' word in lexicon, adding one")
            with codecs.open(dict_file, mode='a', encoding="UTF-8") as out:
                    out.write(u"<unk> SPN\n")
            dict_words.append(u"<unk>")
            transcriptions.append([u"SPN"])
        else:
            unk_transcript = transcriptions[dict_words.index(u"<unk>")]
            assert unk_transcript == [u"SPN"], \
                (
                u"'<unk>' word is reserved for mapping "
                u"OOV items and should always be transcribed "
                u"as 'SPN' (vocal) noise'"
                )
        # Should we log a warning for all words containing silence phones?
        # unused words
        dict_words_set = set(dict_words)
        used_words = [word for words in utt_words for word in words]
        used_word_types = set(used_words)
        used_word_counts = collections.Counter(used_words)
        used_dict_words = set.intersection(dict_words_set, used_word_types)
        log.warning(u"{0} dictionary words used out of {1}".format(len(used_dict_words), len(dict_words_set)))
        # oov words
        oov_word_types = set.difference(used_word_types, dict_words_set)
        oov_word_counts = collections.Counter({oov : used_word_counts[oov] for oov in oov_word_types})
        nb_oov_tokens = sum(oov_word_counts.values())
        nb_oov_types = len(oov_word_types)
        log.warning(u"{0} OOV word types in transcriptions out of {1} types in total".format(nb_oov_types, len(used_word_types)))
        log.warning(u"{0} OOV word tokens in transcriptions out of {1} tokens in total".format(nb_oov_tokens, len(used_words)))
        log.debug(
            (
            u"List of OOV word types with occurences counts: {0}"
            ).format(strcounts2unicode(oov_word_counts.most_common()))
        )
        # raise alarm if the proportion of oov words is too large
        # either in terms of types or tokens
        oov_proportion_types = nb_oov_types/float(len(used_word_types))
        oov_proportion_tokens = nb_oov_tokens/float(len(used_words))
        log.debug(u"Proportion of oov word types: {0}".format(oov_proportion_types))
        log.debug(u"Proportion of oov word tokens: {0}".format(oov_proportion_tokens))
        if oov_proportion_types > 0.1:
            log.info(u"More than 10 percent of word types used are Out-Of-Vocabulary items!")
        if oov_proportion_tokens > 0.1:
            log.info(u"More than 10 percent of word tokens used are Out-Of-Vocabulary items!")
        # homophones (issue warnings only)
        str_transcripts = [u" ".join(phone_trans) for phone_trans in transcriptions]
        counts = collections.Counter(str_transcripts)
        duplicate_transcripts = collections.Counter({trans: counts[trans] for trans in counts if counts[trans] > 1})
        if duplicate_transcripts:
            log.info("There are homophones in the pronunciation dictionary")
            log.warning(
                (
                u"There are {0} phone sequences that correspond to several words "
                u"in the pronunciation dictionary"
                ).format(len(duplicate_transcripts))
            )
            log.warning(
                (
                u"There are {0} word types with homophones "
                u"in the pronunciation dictionary"
                ).format(sum(duplicate_transcripts.values()))
            )
            s = strcounts2unicode(duplicate_transcripts.most_common())
            log.warning(
                (
                u"List of homophonic phone sequences in 'lexicon.txt' "
                u"with number of corresponding word types: {0}"
                ).format(s)
            )
            """
            Commented because it takes a lot of times for certain corpora
            Maybe put it as an option
            # get word types:
            #    - found in transcriptions
            #    - with at least one homophonic word type also found in transcriptions
            homophonic_sequences = duplicate_transcripts.keys()
            homophony_groups = {}
            for homo_transcript in homophonic_sequences:
                homo_group = [word for word, transcript in zip(dict_words, str_transcripts) \
                            if transcript == homo_transcript and word in used_word_types]
                if len(homo_group) > 1:
                    homophony_groups[homo_transcript] = homo_group
            nb_homo_types = sum([len(homo_group) for homo_group in homophony_groups.values()])
            log.warning(
                (
                u"{0} word types found in transcriptions with "
                u"at least one homophone also found in transcriptions "
                u"out of {1} word types in total"
                ).format(nb_homo_types, len(used_word_types))
            )
            nb_homo_tokens = sum([sum([used_word_counts[word] for word in homo_group]) for homo_group in homophony_groups.values()])
            log.warning((u"{0} corresponding word tokens out of {1} total").format(nb_homo_tokens, len(used_words)))
            l = [", ".join([word + u": " + unicode(used_word_counts[word]) for word in group]) for group in homophony_groups.values()]
            s = "\n".join(l)
            log.warning(
                (
                u"List of groups of homophonic word types "
                u"(including only types actually found in transcriptions) "
                u"with number of occurences of each member of each group:\n{0}"
                ).format(s)
            )
            """
        # ooi phones

        used_phones = [phone for trans_phones in transcriptions for phone in trans_phones]
        ooi_phones = [phone for phone in set(used_phones) if not(phone in inventory)]
        if ooi_phones:
            raise IOError(u"Phonetic dictionary uses out-of-inventory phones: {0}".format(ooi_phones))
        # warning for unused phones
        unused_phones = set.difference(inventory, used_phones)
        if unused_phones:
            log.warning(
                (
                u"The following phones are never found "
                u"in the transcriptions: {0}"
                ).format(unused_phones)
            )
        log.debug(u"'lexicon.txt' file is OK")

        # wrap-up
        log.info("Corpus ready for use with abkhazia!!!")

    except (IOError, AssertionError) as e:
        log.error(e)
        raise e

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=\
        (
        "checks whether "
        "a corpus is correctly formatted for use with the abkhazia library"
        )
    )
    parser.add_argument('corpus_path', help=\
        (
        "path to the folder containing the corpus "
        "in abkhazia format"
        )
    )
    parser.add_argument('--verbose', action='store_true', help='verbose flag')
    args = parser.parse_args()
    validate(args.corpus_path, args.verbose)
