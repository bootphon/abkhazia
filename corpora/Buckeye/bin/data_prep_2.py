# coding: utf-8

"""Data preparation for the revised Buckeye corpus (in the original format)

Copyright (C) 2015, 2016 by Thomas Schatz, Xuan Nga Cao, Mathieu Bernard

"""

import abkhazia.corpora

# TODO Change paths of your data in the "Parameters" section

#######################################################################################
#######################################################################################
############################### Some utility functions ################################
#######################################################################################
#######################################################################################

# TODO why librispeech in the comments ?
# If generating the data for the first time, run all steps. Otherwise,
# start from step 6 to just link the wavs rep. (wavs already available
# in /fhgfs/bootphon/data/derived_data/LibriSpeech_abkhazia/data/)

"""
STEP 1
List all files and formats used in corpus
"""
def list_dir(d):
    # filter out .DS_Store files from MacOS if any
    return [e for e in os.listdir(d) if e != '.DS_Store']



#Get list of wav files
def list_wavs(input_dir):
    file_list = []
    for dirpath, dirs, files in os.walk(input_dir):
        for f in files:
              m_file = re.match("(.*)\.wav$", f)
              if m_file:
                  file_list.append(os.path.join(dirpath, f))
    return file_list

#Get list of word files
def list_wrds(input_dir):
    file_list = []
    for dirpath, dirs, files in os.walk(input_dir):
        for f in files:
              m_file = re.match("(.*)\.words_new$", f)
              if m_file:
                  file_list.append(os.path.join(dirpath, f))
    return file_list


#Get list of txt files
def list_utts(input_dir):
    file_list = []
    for dirpath, dirs, files in os.walk(input_dir):
        for f in files:
              m_file = re.match("(.*)\.txt$", f)
              if m_file:
                  file_list.append(os.path.join(dirpath, f))
                  #print (f)
    return file_list


"""
STEP 2
Link speech folder to the data kaldi directory
"""
def link_wavs(wav_path_src, wav_dir, log_dir):
    #if folder already exists and has link, unlink and recreate link
    if os.path.isdir(wav_dir):
        if os.path.islink(wav_dir):
            os.unlink(wav_dir)
            os.symlink(wav_path_src, wav_dir)
        #if folder already exists and is unlinked, remove folder and re-create symbolic link
        else:
            shutil.rmtree(wav_dir)
            os.symlink(wav_path_src, wav_dir)
    #if wavs folder doesn't exist, create symbolic link to speech data
    else:
        os.symlink(wav_path_src, wav_dir)
    print ('finished linking wav files')


"""STEP 3

Create utterance files. It contains the list of all utterances with
the name of the associated wavefiles, and if there is more than one
utterance per file, the start and end of the utterance in that
wavefile expressed in seconds.  "segments.txt": <utterance-id>
<wav-filename> <segment-begin> <segment-end>

"""
def make_segment(utt_dir, wrd_dir, output_file):
    outfile = open (output_file, "w")
    input_txt = list_utts(utt_dir)
    for utts in input_txt:
        length_utt = []
        with open (utts) as infile_txt:
            current_index = 0
            last_offset = 0
            lines = infile_txt.readlines()
            bname = os.path.basename(utts)
            bname_word = bname.replace('txt', 'words_new')
            bname_wav = bname.replace('txt', 'wav')
            utt = bname.replace('.txt', '')
            length_utt = [len(line.strip().split()) for line in lines]
            wrd = os.path.join(wrd_dir, bname_word)
            with open (wrd) as infile_wrd:
                lines_2 = infile_wrd.readlines()
                #print (wrd)
                del lines_2[:9]
                assert len(lines_2) == sum(length_utt), '{} {}'.format(len(lines_2), sum(length_utt))
                for n in range(len(length_utt)):
                    if (n == 0):
                        onset = '0.000'
                        outfile.write(utt + '-sent' + str(n+1) + ' ' + bname_wav + ' ' + onset + ' ')
                        index_offset = length_utt[n]
                        offset_line = lines_2[index_offset-1]
                        match_offset = re.match('\s\s+(.*)\s+(121|122)\s(.*)', offset_line)
                        if not match_offset:
                            print(offset_line)
                            raise IOError
                        offset = match_offset.group(1)
                        outfile.write(str(offset))
                        current_index = index_offset
                        last_offset = offset
                        outfile.write('\n')
                    else:
                        onset = last_offset
                        outfile.write(utt + '-sent' + str(n+1) + ' ' + bname_wav + ' ' + str(onset) + ' ')
                        index_offset = length_utt[n]+current_index
                        offset_line = lines_2[index_offset-1]
                        match_offset = re.match('\s\s+(.*)\s+(121|122)\s(.*)', offset_line)
                        if not match_offset:
                            print(offset_line)
                            raise IOError
                        offset = match_offset.group(1)
                        outfile.write(str(offset))
                        current_index = index_offset
                        last_offset = offset
                        outfile.write('\n')
    print ('finished creating segments file')


"""
STEP 4
Create speaker file. It contains the list of all utterances with a unique identifier for the associated speaker.
"utt2spk.txt": <utterance-id> <speaker-id>
"""
def make_speaker(utt_dir, output_file):
    outfile = open (output_file, "w")
    input_txt = list_utts(utt_dir)
    for utts in input_txt:
        with open (utts) as infile_txt:
            lines = infile_txt.readlines()
            bname = os.path.basename(utts)
            utt = bname.replace('.txt', '')
            speaker_id = re.sub(r"[0-9][0-9](a|b)\.txt", "", bname)
            for idx, val in enumerate(lines, start=1):
               outfile.write(utt + '-sent' + str(idx) + ' ' + speaker_id + '\n')
    print ('finished creating utt2spk file')


"""
STEP 5
Create transcription file. It constains the transcription in word units for each utterance
"text.txt": <utterance-id> <word1> <word2> ... <wordn>
"""
def make_transcription(utt_dir, output_file):
    outfile = open (output_file, "w")
    input_txt = list_utts(utt_dir)
    for utts in input_txt:
        with open (utts) as infile_txt:
            lines = infile_txt.readlines()
            bname = os.path.basename(utts)
            utt = bname.replace('.txt', '')
            for idx, val in enumerate(lines, start=1):
                outfile.write(utt + '-sent' + str(idx) + ' ')
                words = val.split()
                if len(words) > 1:
                    for w in words[:-1]:
                        outfile.write(w + ' ')
                    outfile.write(str(words[-1]) + '\n')
                else:
                    for w in words:
                        outfile.write(w)
                    outfile.write('\n')
    print ('finished creating text file')


"""
STEP 6
The phonetic dictionary contains a list of words with their phonetic transcription
Create phonetic dictionary file, "lexicon.txt": <word> <phone_1> <phone_2> ... <phone_n>
"""
def make_lexicon(wrd_dir, output_file):
    dict_word = {}
    outfile = open (output_file, "w")
    input_txt = list_wrds(wrd_dir)
    for utts in input_txt:
        with open (utts) as infile_txt:
            #for each line of transcription, store the words in a dictionary and increase frequency
            lines = infile_txt.readlines()
            for line in lines:
                line.strip()
                format_match = re.match('\s\s+(.*)\s+(121|122)\s(.*)', line)
                if format_match:
                    word_trs = format_match.group(3)
                    word_format_match = re.match("(.*); (.*); (.*); (.*)", word_trs)
                    if word_format_match:
                        word = word_format_match.group(1)
                        phn_trs = word_format_match.group(3)
                        """
                        Doing some foldings for spoken noise"
                        pattern1 = re.compile("<UNK(.*)")
                        if pattern1.match(word):
                            phn_trs = phn_trs.replace('UNKNOWN', 'SPN')
                        pattern2 = re.compile("<(CUT|cut)(.*)")
                        if pattern2.match(word):
                            phn_trs = phn_trs.replace('CUTOFF', 'SPN')
                        pattern3 = re.compile("<LAU(.*)")
                        if pattern3.match(word):
                            phn_trs = phn_trs.replace('LAUGH', 'SPN')
                        pattern4 = re.compile("<(EXT|EXt)(.*)")
                        if pattern4.match(word):
                            phn_trs = phn_trs.replace('LENGTH_TAG', 'SPN')
                        pattern5 = re.compile("<ERR(.*)")
                        if pattern5.match(word):
                            phn_trs = phn_trs.replace('ERROR', 'SPN')
                        pattern6 = re.compile("<HES(.*)")
                        if pattern6.match(word):
                            phn_trs = phn_trs.replace('HESITATION_TAG', 'SPN')
                        pattern7 = re.compile("<EXCL(.*)")
                        if pattern7.match(word):
                            phn_trs = phn_trs.replace('EXCLUDE', 'SPN')
                        """
                        if word not in dict_word:
                            dict_word[word] = phn_trs

    for w, f in sorted(dict_word.items(), key=lambda kv: kv[1], reverse=True):
        outfile.write (w + ' ' + f + '\n')
    print ('finished creating lexicon file')


"""
STEP 7
The phone inventory contains a list of each symbol used in the pronunciation dictionary
Create phone list file, "phones.txt": <phone-symbol> <ipa-symbol>
"""
def make_phones(phones, data_dir, silences=None, variants=None):
    # code taken from GP_Mandarin... could share it ?
    output_file = os.path.join(data_dir, 'phones.txt')
    with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
        for phone in phones:
            out.write(u"{0} {1}\n".format(phone, phones[phone]))
    if not(silences is None):
        output_file = os.path.join(data_dir, 'silences.txt')
        with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
            for sil in silences:
                out.write(sil + u"\n")
    if not(variants is None):
        output_file = os.path.join(data_dir, 'variants.txt')
        with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
            for l in variants:
                out.write(u" ".join(l) + u"\n")
    print("finished creating phones.txt, silences.txt, variants.txt")


#######################################################################################
#######################################################################################
##################################### Parameters ######################################
#######################################################################################
#######################################################################################

# Raw distribution of the revised Buckeye corpus is available at:
# http://buckeyecorpus.osu.edu/ (TODO change link later when the
# revised version will be distributed)
raw_buckeye_path = "/home/mbernard/data/BUCKEYE_revised_original_format/"


# Path to a directory where the processed corpora is to be stored
# output_dir = "/home/xcao/github_abkhazia/abkhazia/corpora/Buckeye/"
output_dir = "/home/mbernard/dev/abkhazia/corpora/Buckeye/"



#######################################################################################
#######################################################################################
###################################### Main part ######################################
#######################################################################################
#######################################################################################

# setting up some paths and directories
data_dir = os.path.join(output_dir, 'data')
if not os.path.isdir(data_dir):
    os.makedirs(data_dir)
wav_dir = os.path.join(data_dir, 'wavs')
log_dir = os.path.join(output_dir, 'logs')

"""
STEP 2
Link speech folder to the data kaldi directory
"""
wav_path_src = os.path.join(raw_buckeye_path, 'wav')
link_wavs(wav_path_src, wav_dir, log_dir)


"""
STEP 3
Create utterance files. It contains the list of all utterances with the name of the associated wavefiles,
and if there is more than one utterance per file, the start and end of the utterance in that wavefile expressed in seconds.
"segments.txt": <utterance-id> <wav-filename> <segment-begin> <segment-end>
"""
output_file = os.path.join(data_dir, 'segments.txt')
utt_dir = os.path.join(raw_buckeye_path, 'txt')
wrd_dir = os.path.join(raw_buckeye_path, 'words_foldings')
make_segment(utt_dir, wrd_dir, output_file)


"""
STEP 4
Create speaker file. It contains the list of all utterances with a unique identifier for the associated speaker.
"utt2spk.txt": <utterance-id> <speaker-id>
"""
output_file = os.path.join(data_dir, 'utt2spk.txt')
utt_dir = os.path.join(raw_buckeye_path, 'txt')
make_speaker(utt_dir, output_file)


"""
STEP 5
Create transcription file. It constains the transcription in word units for each utterance
"text.txt": <utterance-id> <word1> <word2> ... <wordn>
"""
output_file = os.path.join(data_dir, 'text.txt')
utt_dir = os.path.join(raw_buckeye_path, 'txt')
make_transcription(utt_dir, output_file)


"""
STEP 6
The phonetic dictionary contains a list of words with their phonetic transcription
Create phonetic dictionary file, "lexicon.txt": <word> <phone_1> <phone_2> ... <phone_n>
"""
output_file = os.path.join(data_dir, 'lexicon.txt')
wrd_dir = os.path.join(raw_buckeye_path, 'words_foldings')
make_lexicon(wrd_dir, output_file)


"""
STEP 7
The phone inventory contains a list of each symbol used in the pronunciation dictionary
Create phone list file, "phones.txt": <phone-symbol> <ipa-symbol>
"""

# get IPA transcriptions for all phones
#The following phones are never found in the transcriptions: set([u'own', u'ahn', u'ihn', u'ayn', u'NSN', u'eyn', u'oyn', u'ehn', u'iyn', u'B', u'E', u'uhn', u'aon', u'awn', u'uwn', u'aan', u'ern', u'aen'])
#Reason: we already collapsed them in the foldings_version
Buckeye_phones = [
    ('iy', u'iː'),
    ('ih', u'ɪ'),
    ('eh', u'ɛ'),
    ('ey', u'eɪ'),
    ('ae', u'æ'),
    ('aa', u'ɑː'),
    ('aw', u'aʊ'),
    ('ay', u'aɪ'),
    ('ah', u'ʌ'),
    ('ao', u'ɔː'),
    ('oy', u'ɔɪ'),
    ('ow', u'oʊ'),
    ('uh', u'ʊ'),
    ('uw', u'uː'),
    ('er', u'ɝ'),
    ('jh', u'ʤ'),
    ('ch', u'ʧ'),
    ('b', u'b'),
    ('d', u'd'),
    ('g', u'g'),
    ('p', u'p'),
    ('t', u't'),
    ('k', u'k'),
    ('dx', u'ɾ'),
    ('s', u's'),
    ('sh', u'ʃ'),
    ('z', u'z'),
    ('zh', u'ʒ'),
    ('f', u'f'),
    ('th', u'θ'),
    ('v', u'v'),
    ('dh', u'ð'),
    ('m', u'm'),
    ('n', u'n'),
    ('ng', u'ŋ'),
    ('em', u'm\u0329'),
    ('nx', u'ɾ\u0303'),
    ('en', u'n\u0329'),
    ('eng', u'ŋ\u0329'),
    ('l', u'l'),
    ('r', u'r'),
    ('w', u'w'),
    ('y', u'j'),
    ('hh', u'h'),
    ('el', u'l\u0329'),
    ('tq', u'ʔ'),
    ('B', u'B'),
    ('E', u'E'),
    ('ahn', u'ʌ\u0329'),
    ('iyn', u'iː\u0329'),
    ('eyn', u'eɪ\u0329'),
    ('oyn', u'ɔɪ\u0329'),
    ('ehn', u'ɛ\u0329'),
    ('uhn', u'ʊ\u0329'),
    ('ayn', u'aɪ\u0329'),
    ('own', u'oʊ\u0329'),
    ('awn', u'aʊ\u0329'),
    ('aon', u'ɔː\u0329'),
    ('aan', u'ɑː\u0329'),
    ('ihn', u'ɪ\u0329'),
    ('ern', u'ɝ\u0329'),
    ('uwn', u'uː\u0329'),
    ('aen', u'æ\u0329'),
    ('aan', u'ɑː\u0329'),
    ('{B_TRANS}', u'{B_TRANS}'),
    ('{E_TRANS}', u'{E_TRANS}'),
    ('CUTOFF', u'CUTOFF'),
    ('ERROR', u'ERROR'),
    ('EXCLUDE', u'EXCLUDE'),
    ('UNKNOWN_WW', u'UNKNOWN_WW'),
    ('UNKNOWN', u'UNKNOWN'),
    ('VOCNOISE', u'VOCNOISE'),
    ('HESITATION_TAG', u'HESITATION_TAG'),
    ('LENGTH_TAG', u'LENGTH_TAG'),
    ('VOCNOISE_WW', u'VOCNOISE_WW'),
    ('NOISE', u'NOISE'),
    ('NOISE_WW', u'NOISE_WW'),
    ('IVER', u'IVER'),
    ('LAUGH', u'LAUGH'),
    ('HESITATION_TAG', u'HESITATION_TAG'),
]
phones = {}
for phone, ipa in Buckeye_phones:
    phones[phone] = ipa
silences = [u"SIL_WW", u"NSN"]  # SPN and SIL will be added automatically
variants = []  # could use lexical stress variants...
make_phones(phones, data_dir, silences, variants)
