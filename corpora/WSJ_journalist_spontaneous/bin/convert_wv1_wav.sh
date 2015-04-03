#convert all wv1 files to wav files and move them to wav folder
cd /fhgfs/bootphon/data/derived_data/new_WSJ_abkhazia/WSJ_journalist_spontaneous/
mkdir -p wavs
cd /fhgfs/bootphon/data/derived_data/new_WSJ_abkhazia/WSJ_journalist_spontaneous/wv1/
#Convert all sphere files into wav files (use sph2pipe available in kaldi)
for i in *.wv1; do /cm/shared/apps/kaldi/tools/sph2pipe_v2.5/sph2pipe -f wav $i >> $i.wav; done
#Rename the ".wv1.wav" extension to ".wav" extension:
for file in *.wav; do mv "$file" "${file/\.wv1\.wav/.wav}"; done	
#move all wav files to wavs folder
mv *.wav ../wavs/
