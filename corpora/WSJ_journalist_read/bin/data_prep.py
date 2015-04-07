# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 00:17:47 2015

@author: Thomas Schatz
"""

"""
Data preparation WSJ for journalist read
"""

import os
import subprocess
import re
import shutil



# paths - needs to change paths and versions of WSJ
# create 'data' directory if doesn't exist
# phones.txt should be distributed?
raw_path = "/fhgfs/bootphon/data/raw_data/WSJ_LDC/"
derived_path = "/fhgfs/bootphon/data/derived_data/new_WSJ_abkhazia/WSJ_journalist_read/"
dict_path = "/fhgfs/bootphon/data/raw_data/CMU_dict/"
abkhazia_path_data = "/fhgfs/bootphon/scratch/xcao/github_abkhazia/abkhazia/corpora/WSJ_journalist_read/data/"
abkhazia_path = "/fhgfs/bootphon/scratch/xcao/github_abkhazia/abkhazia/corpora/WSJ_journalist_read/"


#######################################################################################
#######################################################################################
############################### Some utility functions ################################
#######################################################################################
#######################################################################################

#If generating the data for the first time, run all steps
#Otherwise, start from step 4 to just link the wavs rep. (wavs already available in /fhgfs/bootphon/data/derived_data/new_WSJ_abkhazia/WSJ_journalist_read/)
#besides, paths, needs to change regex to extract the correct files for appropriate corpus

#STEP 1
# filter out .DS_Store files from MacOS if any
def list_dir(d):
	return [e for e in os.listdir(d) if e != '.DS_Store']


#STEP 2
#copy all wv1 files into one wv1 directory in "derived data"
#copy all transcription files to "derived data"
#Arguments are wv1 (o) and trs (o2) folders
def copy_wv1_trs(o, o2):
    array_good_dir =[]
    #create wirs dir
    output_dir = os.path.join(derived_path, o)
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    #create trs dir
    output_dir2 = os.path.join(derived_path, o2)
    if not os.path.isdir(output_dir2):
        os.makedirs(output_dir2)
    #walk recursively and find the directories for j_read: si_tr_j and "c"
     #needs to change regex to find the correct files
    for dirpath, dirs, files in os.walk(raw_path):
        for d in dirs:
            d_match = re.match("si_tr_j", d)
            if d_match:
                good_dir = os.path.join(dirpath,d)
                array_good_dir.append(good_dir)
    #Only walk through j_read directories and copy all "c" wv1 files (XXXc...) to temp wv1 folder
    for d in array_good_dir:
        for dirpath2, dirs2, files2 in os.walk(d):
            for f in files2:
                m_file = re.match("^([0-9a-z][0-9a-z][0-9a-z])c(.*)\.wv1", f)
                if m_file:
                    filename = os.path.join(dirpath2,f)
                    dest_filename = os.path.join(output_dir,f)
                    shutil.copy2(filename, dest_filename)
                    print ('finished copying wv1' + filename)
                m_trs = re.match("^([0-9a-z][0-9a-z][0-9a-z])c(.*)\.dot", f)
                if m_trs:
                    filename = os.path.join(dirpath2,f)
                    dest_filename = os.path.join(output_dir2,f)
                    shutil.copy2(filename, dest_filename)
                    print ('finished copying trs' + filename)
                    

#STEP 3
#call shell script to convert all flac files to wav files
def convert_wv1():
    #needs to change path in convert_wv1_wav.sh - may also need to change rights for the shell script in order to execute it
    subprocess.call("./convert_wv1_wav.sh", shell=True)
    wv1_dir = os.path.join(derived_path, "wv1")
    #remove wv1 folder
    shutil.rmtree(wv1_dir)
    print ('finished converting wv1 files to wav files and moving them to wavs directory')


#STEP 4
#link speech folder to the data kaldi directory
def link_wavs():
    wavs_path = os.path.join(abkhazia_path_data, "wavs")
    wavs_path_src = os.path.join(derived_path, 'wavs')
    logs_path = os.path.join(abkhazia_path, "logs")
    #if wavs folder doesn't exist, create symbolic link to speech data
    if not os.path.isdir(wavs_path):
        os.symlink(wavs_path_src, wavs_path)
    #if already exists, remove folder and all files and re-create symbolic link to speech data
    else:
        #unlink folder
        os.unlink(wavs_path)
        #remove folder
        shutil.rmtree(wavs_path, ignore_errors=True)
        #create symlink
        os.symlink(wavs_path_src, wavs_path)
    #if logs folder doesn't exist, create folder
    if not os.path.isdir(logs_path):
        os.makedirs(logs_path)
    print ('finished linking wavs directory and creating logs directory')


#STEP 5
#Create segments file: <utterance-id> <wav-filename>
#Create speakers file: <utterance-id> <speaker-id>
#Argument is name of wav directory
def segments_text_speakers():
    utt_list = []
    output_file_segment = open(os.path.join(abkhazia_path_data, 'segments.txt'), 'w')
    output_file_speaker = open(os.path.join(abkhazia_path_data, 'utt2spk.txt'), 'w')
    output_file_text = open(os.path.join(abkhazia_path_data, 'text.txt'), 'w')
    output_file_temp = open(os.path.join(abkhazia_path, 'logs/temp.txt'), 'w')
    input_dir_wav = os.path.join(derived_path, "wavs")
    input_dir_trs = os.path.join(derived_path, "trs")
    #list all files in wav folder
    files = os.listdir(input_dir_wav)
    #get basename from file to get utt_ID
    for filename in files:
        utt_ID = os.path.splitext(filename)[0]
		#create a list with all utt_ID
        utt_list.append(utt_ID)
        #write segments file
        output_file_segment.write(utt_ID + ' ' + filename + '\n')
        #extract the first 3 characters from filename to get speaker_ID
        m_speaker = re.match("^([0-9a-z][0-9a-z][0-9a-z])c(.*)\.wav", filename)
        if m_speaker:
            speaker_ID = m_speaker.group(1)
            #write utt2spk file
            output_file_speaker.write(utt_ID + ' ' + speaker_ID + '\n')
    print ('finished creating segments and speakers files')
    files_trs = os.listdir(input_dir_trs)
    for filename2 in files_trs:
        infile = open(os.path.join(input_dir_trs, filename2), 'r')
        for line in infile:
            m_line = re.match("(.*) \((.*)\)", line)
            if m_line:
                utt = m_line.group(1)
                ID = m_line.group(2)
				#ID doesn't match from list of files, skip (this is to deal with utterances that have only noise)
                if ID not in utt_list:
                    print(ID)
                    continue
                else:
                    words = utt.split()
                    output_file_temp.write(ID + ' ')
                    for w in words:
                        w = w.upper() # Upcase everything to match the CMU dictionary
                        w = w.replace("\\", "") #Remove backslashes.  We don't need the quoting
                        w = w.replace("%PERCENT", "PERCENT") # Normalization for Nov'93 test transcripts.
                        w = w.replace(".POINT", "POINT") # Normalization for Nov'93 test transcripts.
                        match1 = re.match("\[<(.*)\]", w)
                        #| \[(.*)\>\] | \[(.*)\/\] | \[\/(.*)/]"),
                        # E.g. [<door_slam], this means a door slammed in the preceding word. Delete
                        # E.g. [door_slam>], this means a door slammed in the next word.  Delete.
                        # E.g. [phone_ring/], which indicates the start of this phenomenon.
                        # E.g. [/phone_ring], which indicates the end of this phenomenon.
                        if match1:
                            #print ("match 1")
                            continue                # we won't print this word.
                        elif((w == "~")|(w == ".")):
                            continue
                        # "~" This is used to indicate truncation of an utterance.  Not a word.
                        # "." is used to indicate a pause.  Silence is optional anyway so not much point including this in the transcript.
                        else:
                            match2 = re.match("\[(.*)\>\]", w)
                            if match2:
                                continue
                            else:
                                match3 = re.match ("\[(.*)/\]", w)
                                if match3:
                                    continue
                                else:
                                    match4 = re.match ("\[\/(.*)\]", w)
                                    if match4:
                                        continue
                                    else:
                                        n_match = re.match("\[(.*)\]", w) # Other noises, e.g. [loud_breath].:
                                        if n_match:
                                            noise = n_match.group(1)
                                            n = noise.replace(noise, '<NOISE>') 
                                            output_file_temp.write(n + ' ')
                                        else:
                                            bracket_match = re.match("\<(.*)\>", w)  # e.g. replace <and> with and.  (the <> means verbal deletion of a word).. but it's pronounced.
                                            if bracket_match:
                                                no_bracket = bracket_match.group(1)
                                                output_file_temp.write(no_bracket + ' ')
                                            else:
                                                dash_match = re.match("--DASH", w)
                                                if dash_match:
                                                    w = w.replace("--DASH", "-DASH")
                                                    output_file_temp.write(w + ' ') # This is a common issue; the CMU dictionary has it as -DASH.
                                                else:
                                                    output_file_temp.write(w + ' ')
                    output_file_temp.write('\n')
    output_file_temp.close()
    infile2 = open(os.path.join(abkhazia_path, 'logs/temp.txt'), 'r')
    for line in infile2:
        line = line.rstrip()
        output_file_text.write(line + '\n')
    print ('finished creating text files')
    infile2.close()
    os.remove(os.path.join(abkhazia_path, 'logs/temp.txt'))
        
                
def lexicon():
    dict_word = {}
    outfile_lexicon = open(os.path.join(abkhazia_path_data, 'lexicon.txt'), 'w')
    outfile_OOV = open (os.path.join(abkhazia_path, 'logs/OOV.txt'), 'w')
    infile = open(os.path.join(abkhazia_path_data, 'text.txt'), 'r')
    #for each line of transcription, store the words in a dictionary and increase frequency
    for line in infile:
        m = re.match("([0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z])\s(.*)", line)
        if m:
            utt = m.group(2)
            #print(utt)
            words = utt.split()
            for word in words:
                if word not in dict_word:
                    dict_word[word] = 1
                else:
                    dict_word[word] += 1
    infile.close()
    #To generate the lexicon, we will use the cmu dict)
    infile2 = open(os.path.join(dict_path, 'cmudict.0.7a'), 'r')
    cmu_dict = {}
    outfile_lexicon.write('<NOISE> NSN' + '\n')
    for line in infile2:
        dictionary = re.match("(.*)\s\s(.*)", line)
        if dictionary:
            entry = dictionary.group(1)
            phn = dictionary.group(2)
            #remove pronunciation variants
            phn = phn.replace("0", "")
            phn = phn.replace("1", "")
            phn = phn.replace("2", "")
            #create the cmu dict with entry and phonetic transcription
            cmu_dict[entry] = phn;
    #Loop through the words in transcripts by descending frequency and create the lexicon by looking up in the combined dictionary
    #if still OOV, output to OOV.txt
    for w, f in sorted(dict_word.items(), key=lambda kv: kv[1], reverse=True):
        if w in cmu_dict.viewkeys():
            outfile_lexicon.write (w + ' ' + cmu_dict[w] + '\n')
        else:
            outfile_OOV.write(w + '\t' + str(f) + '\n')
    print ('finished creating lexicon file')
         


#Running the different steps
#copy_wv1_trs ('wv1', 'trs')
#convert_wv1()
#link_wavs()
segments_text_speakers()
#lexicon()

	




