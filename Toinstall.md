- ./install_kaldi.sh
 sudo apt-get install gawk
 -Insttall SRILM
Simply running /tools/extras/install_srilm.sh cannot install srilm automatically.
The right procedure is as follows.
Download srilm package from http://www.speech.sri.com/projects/srilm/download.html.
Rename the package as “srilm.tgz”.
Copy the package to /tools.
Run /tools/extras/install_srilm.sh.
Source /tools/env.sh.

-Searching for matplotlib
Reading https://pypi.python.org/simple/matplotlib/
Couldn't find index page for 'matplotlib' (maybe misspelled?)
Scanning index of all packages (this may take a while)
Reading https://pypi.python.org/simple/
No local packages or download links found for matplotlib
error: Could not find suitable distribution for Requirement.parse('matplotlib')

sudo pip3 install -U setuptools
sudo pip3 install -U jinja2
sudo pip3 install phonemizer
pip3 install matplotlib
sudo pip3 install progressbar2
sudo pip3 install h5features
sudo pip3 install argcomplete

python 3.8
h5py==2.10.0
