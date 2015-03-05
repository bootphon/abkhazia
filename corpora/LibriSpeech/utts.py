import os, sys
from joblib import Parallel, delayed

#folder = '/fhgfs/bootphon/scratch/gsynnaeve/librivox/LibriSpeech/'
folder = '/fhgfs/bootphon/scratch/gsynnaeve/librivox/LibriSpeech/train-clean-100/'
todo = []
with open('segments', 'w') as wf:
    for bdir, _, files in os.walk(folder):
        for fname in files:
            if fname[-4:] == 'flac':
                ffname = bdir.rstrip(' /') + '/' + fname.strip()
                wfname = fname.split('.')[0] + '.wav'
                spkrid = wfname.split('-')[0]
                s = int(spkrid)
                spkrid = "%05d" % s
                sdir = 'data/' + spkrid
                if not os.path.exists(sdir):
                    os.mkdir(sdir)
                wavfname = sdir + '/' + spkrid + '-' + '-'.join(wfname.split('-')[1:])
                print ffname, wavfname
                cmd = 'sox -b 16 ' + ffname + ' ' + wavfname + ' rate 16k'
                todo.append(cmd)
                wf.write(wavfname.split('/')[-1].split('.')[0] + ' ' + wavfname.split('/')[-1] + '\n')
print "WROTE segments"
with open('segments') as rf:
    with open('utt2spk', 'w') as wf:
        for line in rf:
            l = line.split()[0]
            wf.write(l + ' ' + l.split('-')[0] + '\n') 
print "WROTE utt2spkr"

Parallel(n_jobs=16, verbose=5)(delayed(os.system)(cmd) for cmd in todo)
