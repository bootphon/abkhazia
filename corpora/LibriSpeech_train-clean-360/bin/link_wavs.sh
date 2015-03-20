#linking wavs folder in the data rep and creating logs folder
ln -s /fhgfs/bootphon/data/derived_data/LibriSpeech_abkhazia/data/wav_train-clean-100/ ../data/
mv ../data/wav_train-clean-100 ../data/wavs
mkdir ../logs
