#linking wavs folder in the data rep and creating logs folder
#change path of link
rm ../data/wavs
ln -s /fhgfs/bootphon/data/derived_data/LibriSpeech_abkhazia/data/wav_train-clean-360/ ../data/
mv ../data/wav_train-clean-360 ../data/wavs
mkdir -p ../logs
