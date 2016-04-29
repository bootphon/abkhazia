#!/bin/bash

cd /home/mbernard/data/abkhazia/brent/align/
source ./path.sh

#lattice-to-post
#gmm-post-to-gpost

# MAYBE
#post-to-phone-post

# YES
get-post-on-ali

exit
dir=$(readlink -f ./exp/ali_fmllr)
ali-to-post "ark,t:gunzip -c $dir/ali.1.gz|" ark,t:$dir/post.1
