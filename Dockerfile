FROM ubuntu:16.04

# install sotware dependencies
RUN apt-get update && apt-get install -y \
        automake \
        autoconf \
        bzip2 \
        clang \
        espeak \
        festival \
        flac \
        g++ \
        gcc \
        gfortran \
        git \
        gzip \
        libatlas3-base \
        libtool \
        make \
        perl \
        python \
        python-h5py \
        python-joblib \
        python-matplotlib \
        python-numpy \
        python-pip \
        python-pytest \
        python-scipy \
        python-setuptools \
        python-sphinx \
        sox \
        subversion \
        vim \
        wget \
        zlib1g-dev
RUN ln -s -f bash /bin/sh

# install shorten
WORKDIR /shorten
RUN wget http://shnutils.freeshell.org/shorten/dist/src/shorten-3.6.1.tar.gz
RUN tar xzf shorten-3.6.1.tar.gz
WORKDIR /shorten/shorten-3.6.1
RUN ./configure
RUN make
RUN make install
WORKDIR /
RUN rm -rf /shorten

# clone abkhazia sources
WORKDIR /abkhazia
RUN git clone https://github.com/bootphon/abkhazia.git .

# install Kaldi
WORKDIR /abkhazia/kaldi
RUN git clone --branch abkhazia --single-branch https://github.com/bootphon/kaldi.git .
WORKDIR /abkhazia/kaldi/tools
RUN ./extras/check_dependencies.sh
RUN make -j4
RUN ./extras/install_openblas.sh
WORKDIR /abkhazia/kaldi/src
RUN ./configure --shared --openblas-root=../tools/OpenBLAS/install
RUN sed -i "s/\-g # -O0 -DKALDI_PARANOID.*$/-O3 -DNDEBUG/" kaldi.mk
RUN make depend -j4
RUN make -j4

# install IRSTLM
WORKDIR /abkhazia/kaldi/tools
RUN apt-get install -y gawk
RUN ./extras/install_irstlm.sh

# install SRILM
WORKDIR /abkhazia/kaldi/tools
RUN wget https://github.com/denizyuret/nlpcourse/raw/master/download/srilm-1.7.0.tgz -O srilm.tgz
RUN ./extras/install_srilm.sh

# cleanup to reduce container size
RUN rm -f *.tgz *.tar.gz *.tar.bz2

# install and test abkhazia
WORKDIR /abkhazia
RUN KALDI_PATH=./kaldi ./configure
RUN python setup.py build
RUN python setup.py install
