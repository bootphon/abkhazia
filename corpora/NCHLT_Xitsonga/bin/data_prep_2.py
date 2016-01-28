# coding: utf-8

"""Data preparation for the Xitsonga corpus

Copyright (C) 2015, 2016 by Thomas Schatz, Xuan Nga Cao, Mathieu Bernard

"""

import abkhazia.corpora

# TODO Change paths of your data in the "Parameters" section

#######################################################################################
#######################################################################################
############################### Some utility functions ################################
#######################################################################################
#######################################################################################

"""
STEP 1
List all files and formats used in corpus
"""
def list_dir(d):
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

#Get list of transcription files
def list_trs(input_dir):
    file_list = []
    for dirpath, dirs, files in os.walk(input_dir):
        for f in files:
              m_file = re.match("(.*)\.xml$", f)
              if m_file:
                  file_list.append(os.path.join(dirpath, f))
    return file_list

#Get list of mlf files
def list_mlf(input_dir):
    file_list = []
    for dirpath, dirs, files in os.walk(input_dir):
        for f in files:
              m_file = re.match("(.*)nchlt\.mlf$", f)
              if m_file:
                  file_list.append(os.path.join(dirpath, f))
    return file_list

"""
STEP 2
Link speech folder to the data kaldi directory and also rename the wav files
"""
def link_wavs(wav_src, wav_dir, log_dir):
    input_wav = list_wavs(wav_src)
    if os.path.isdir(wav_dir):
        shutil.rmtree(wav_dir)
        os.makedirs(wav_dir)
        for wav_file in input_wav:
            bname = os.path.basename(wav_file)
            #rename all wav files so that wav files start by speaker_ID
            short_bname = bname.replace('nchlt_tso_', '')
            path_shortname = os.path.join(wav_dir, short_bname)
            os.symlink(wav_file, path_shortname)
    print ('finished linking wav files')



"""STEP 3

Create utterance files. It contains the list of all utterances with
the name of the associated wavefiles, and if there is more than one
utterance per file, the start and end of the utterance in that
wavefile expressed in seconds.  "segments.txt": <utterance-id>
<wav-filename>

"""
def make_segment(wav_dir, output_file):
    outfile = open (output_file, "w")
    input_wav = list_wavs(wav_dir)
    for wav_file in input_wav:
        bname = os.path.basename(wav_file)
        utt_id = bname.replace('.wav', '')
        outfile.write(utt_id + ' ' + bname + '\n')
    print ('finished creating segments file')



"""
STEP 4
Create speaker file. It contains the list of all utterances with a unique identifier for the associated speaker.
"utt2spk.txt": <utterance-id> <speaker-id>
"""
def make_speaker(wav_dir, output_file):
    outfile = open (output_file, "w")
    input_wav = list_wavs(wav_dir)
    for wav_file in input_wav:
        bname = os.path.basename(wav_file)
        utt_id = bname.replace('.wav', '')
        #extract the first 3 characters from filename to get speaker_ID
        m_speaker = re.match("(.*)_(.*)", bname)
        if m_speaker:
            speaker_id = m_speaker.group(1)
            outfile.write(utt_id + ' ' + speaker_id + '\n')
    print ('finished creating utt2spk file')


"""
STEP 5
Create transcription file. It constains the transcription in word units for each utterance
"text.txt": <utterance-id> <word1> <word2> ... <wordn>
"""
def make_transcription(segment_file, trs_dir, output_file):
    list_utt = []
    list_info = []
    list_total = []
    outfile = open (output_file, "w")
    infile_seg = open (segment_file, "r")
    #get all the utt ID to make sure that the trs match with the wav files
    for line in infile_seg:
        m_segment = re.match('(.*) (.*)', line)
        if m_segment:
            utt =  m_segment.group(1)
            list_utt.append(utt)
    infile_seg.close()

    input_txt = list_trs(trs_dir)
    for utts in input_txt:
        with open (utts) as infile_txt:
            #store each file as one string and split by tag
            data = ' '.join([line.replace('\n', '') for line in infile_txt.readlines()])
            list_info = data.split('</recording>')
            #append the list to the main list
            list_total.extend(list_info)
    print ("finished extracting the recording tags")
    #Go through each recording and extract the text and utt_ID according to pattern
    for i in list_total:
        m_text = re.match("(.*)<recording audio=(.*).wav(.*)<orth>(.*)</orth>", i)
        if m_text:
            utt_ID = m_text.group(2)
            text = m_text.group(4)
            #remove beginning of wav path to have utt_ID
            utt_ID = re.sub("(.*)nchlt_tso_", "", utt_ID)
            #replace [s] by <NOISE>
            text = text.replace("[s]", "<NOISE>")
            #check that the text has the equivalent wav and write to outfile
            if utt_ID in list_utt:
                outfile.write(utt_ID + ' ' + text + '\n')
            else:
                print(utt_ID)
    print ('finished creating text file')



"""
STEP 6
The phonetic dictionary contains a list of words with their phonetic transcription
Create phonetic dictionary file, "lexicon.txt": <word> <phone_1> <phone_2> ... <phone_n>
To do this, we need to get the mlfs for the language. Not sure it is available on the NCHLT website.
"""

def make_lexicon(outfile_lexicon, outfile_temp, mlf_dir):
    list_total = []
    list_file = []
    list_line = []
    list_word = []
    list_phn = []
    dict_word = {}
    out_lex = open (outfile_lexicon, "w")
    out_temp = open (outfile_temp, "w")
    input_mlf = list_mlf(mlf_dir)
    for mlfs in input_mlf:
        with open (mlfs) as infile_mlf:
            #join all lines together into one string but still keeping new line character
            data = '\n'.join([line.replace('\n', '') for line in infile_mlf.readlines()])
            #split into a list of files ("." is the separator)
            list_file = re.split('\.\n', data)
            #increment the total list which will be a list containing all small files
            list_total.extend(list_file)
        infile_mlf.close()
    #Go through each small file
    for i in list_total:
        #split into a list of words (separator is "[0-9]+ [0-9]+ sp (.*)")
        list_word = re.split('[0-9]+ [0-9]+ sp (.*)', i)
        for w in list_word:
            w = w.strip()
            #split into lines
            list_line = w.split('\n')
            for l in list_line:
                #split each line into tokens
                list_phn = l.split()
                #if the line contains the word, extract word + phone
                if (len(list_phn) == 5):
                    #exclude the silence word
                    if (list_phn[4] == 'SIL-ENCE'):
                        continue
                    #otherwise, extract just phone corresponding to word already extracted
                    else:
                        out_temp.write(list_phn[4] + '\t' + list_phn[2])
                elif (len(list_phn) == 4):
                    out_temp.write(' ' + list_phn[2])
            out_temp.write('\n')
    out_temp.close()
    print ('finished writing temp file')

    #open temp dictionary
    in_temp = open (outfile_temp, "r")
    #add these 2 entries in the dict
    out_lex.write ('<noise> NSN\n')
    out_lex.write ('<unk> SPN\n')
    out_lex.write ('<NOISE> NSN\n')
    for line in in_temp:
        line = line.strip()
        m_file = re.match("(.*)\t(.*)", line)
        if m_file:
            word = m_file.group(1)
            phn = m_file.group(2)
            #if word not in the lexicon, add entry
            if word not in dict_word:
                if (word == "[s]"):
                    continue
                else:
                    dict_word[word] = phn
    #write lexicon to file, sorted by alphabetical order
    for w in sorted(dict_word):
            out_lex.write (w + ' ' + dict_word[w] + '\n')
    in_temp.close()
    print ('finished creating lexicon file')
    #remove temp file
    os.remove(outfile_temp)


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

# Raw distribution of Xitsonga is available at http://rma.nwu.ac.za/index.php/resource-catalogue/nchlt-speech-corpus-ts.html (free)
# raw_Xitsonga_path = "/home/xcao/cao/multilingual/African_languages/Xitsonga/raw_corpus/nchlt_Xitsonga"
raw_Xitsonga_path = "/home/mbernard/data/nchlt_Xitsonga"

# Path to a directory where the processed corpora is to be stored
# output_dir = "/home/xcao/github_abkhazia/abkhazia/corpora/NCHLT_Xitsonga/"
output_dir = "/home/mbernard/dev/abkhazia/corpora/NCHLT_Xitsonga/"


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
if not os.path.isdir(wav_dir):
    os.makedirs(wav_dir)
log_dir = os.path.join(output_dir, 'logs')
if not os.path.isdir(log_dir):
    os.makedirs(log_dir)

"""
STEP 2
Link speech folder to the data kaldi directory
"""
wav_path_src = os.path.join(raw_Xitsonga_path, 'audio')
link_wavs(wav_path_src, wav_dir, log_dir)


"""
STEP 3
Create utterance files. It contains the list of all utterances with the name of the associated wavefiles,
and if there is more than one utterance per file, the start and end of the utterance in that wavefile expressed in seconds.
"segments.txt": <utterance-id> <wav-filename> <segment-begin> <segment-end>
"""
output_file = os.path.join(data_dir, 'segments.txt')
wav_dir = os.path.join(data_dir, 'wavs')
make_segment(wav_dir, output_file)


"""
STEP 4
Create speaker file. It contains the list of all utterances with a unique identifier for the associated speaker.
"utt2spk.txt": <utterance-id> <speaker-id>
"""
output_file = os.path.join(data_dir, 'utt2spk.txt')
wav_dir = os.path.join(data_dir, 'wavs')
make_speaker(wav_dir, output_file)



"""
STEP 5
Create transcription file. It constains the transcription in word units for each utterance
"text.txt": <utterance-id> <word1> <word2> ... <wordn>
"""
segment_file = os.path.join(data_dir, 'segments.txt')
trs_dir = os.path.join(raw_Xitsonga_path, 'transcriptions')
output_file = os.path.join(data_dir, 'text.txt')
make_transcription(segment_file, trs_dir, output_file)


"""
STEP 6
The phonetic dictionary contains a list of words with their phonetic transcription
Create phonetic dictionary file, "lexicon.txt": <word> <phone_1> <phone_2> ... <phone_n>
"""
outfile_lexicon = os.path.join(data_dir, 'lexicon.txt')
outfile_temp = os.path.join(log_dir, 'temp.txt')
mlf_dir = os.path.join(raw_Xitsonga_path, 'mlfs_tso')
make_lexicon(outfile_lexicon, outfile_temp, mlf_dir)


"""
STEP 7
The phone inventory contains a list of each symbol used in the pronunciation dictionary
Create phone list file, "phones.txt": <phone-symbol> <ipa-symbol>
# get IPA transcriptions for all phones
"""
Xitsonga_phones = [
    ('n\'', u'ɳ'),
    ('K', u'ɬ'),
    ('tl_>', u'tl\''),
    ('tl_h', u'tlʰ'),
    ('d', u'd'),
    ('E', u'Ɛ'),
    ('a', u'a'),
    ('gh\\', u'gɦ'),
    ('j', u'j'),
    ('tj_h', u'tjʰ'),
    ('u', u'u'),
    ('d_0Z', u'ʤ'),
    ('k', u'k'),
    ('g', u'g'),
    ('pj_h', u'pjʰ'),
    ('dz`h\\', u'dʐɦ'),
    ('dZh\\', u'ʤh'),
    ('J', u'ɲ'),
    ('n_h', u'nɦ'),
    ('tj', u'tj'),
    ('bj', u'bj'),
    ('v', u'v'),
    ('B', u'β'),
    ('s', u's'),
    ('S', u'ʃ'),
    ('k_h', u'kʰ'),
    ('pj_>', u'pj\''),
    ('tS_>', u'ts\ʼ'),
    ('tS_h', u'tsʰ'),
    ('b', u'b'),
    ('z', u'z'),
    ('dz`', u'dʐ'),
    ('b_<', u'ɓ'),
    ('w', u'w'),
    ('r', u'r'),
    ('t_h', u'tʰ'),
    ('rh\\', u'rɦ'),
    ('m_h', u'mɦ'),
    ('s`', u'ʂ'),
    ('p_h', u'pʰ'),
    ('f', u'f'),
    ('i', u'i'),
    ('dh\\', u'dɦ'),
    ('h\\', u'ɦ'),
    ('O', u'ɔ'),
    ('n', u'n'),
    ('N', u'ŋ'),
    ('dK\\', u'dɮ'),
    ('dK', u'dɬ'),
    ('!\\', u'!'),
    ('m', u'm'),
    ('dj', u'dj'),
    ('l', u'l'),
    ('p', u'p'),
    ('t_>', u't\''),
]
phones = {}
for phone, ipa in Xitsonga_phones:
    phones[phone] = ipa
silences = [u"NSN"]  # SPN and SIL will be added automatically
variants = []  # could use lexical stress variants...
make_phones(phones, data_dir, silences, variants)
print("Created phones.txt, silences.txt, variants.txt")
