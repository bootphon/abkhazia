#convert all flac files to wav files and move them to wav folder
cd /fhgfs/bootphon/data/derived_data/LibriSpeech_abkhazia/data/
mkdir wav_train-clean-100
cd /fhgfs/bootphon/data/derived_data/LibriSpeech_abkhazia/data/flac_train-clean-100/
for i in *.flac ; do flac -d $i ; done
mv *.wav ../wav_train-clean-100/
