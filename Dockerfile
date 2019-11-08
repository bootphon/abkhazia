FROM ubuntu:16.04

# install sotware dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
        automake \
        autoconf \
        bzip2 \
        clang \
        espeak \
        festival \
        flac \
        g++ \
        gawk \
        gcc \
        gfortran \
        git \
        gzip \
        libatlas3-base \
        libtool \
        make \
        patch \
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
        wget \
        zlib1g-dev && \
        rm -rf /var/lib/apt/lists/*

# install shorten
RUN wget http://shnutils.freeshell.org/shorten/dist/src/shorten-3.6.1.tar.gz && \
        tar xzf shorten-3.6.1.tar.gz && \
        cd shorten-3.6.1 && \
        ./configure && \
        make && \
        make install && \
        cd - && \
        rm -rf shorten*

# install Kaldi, IRSTLM and SRILM
WORKDIR /kaldi
RUN git clone --branch abkhazia --single-branch https://github.com/bootphon/kaldi.git . && \
        ln -s -f bash /bin/sh && \
        cd /kaldi/tools && \
        ./extras/check_dependencies.sh && \
        make -j4 && \
        ./extras/install_openblas.sh && \
        cd /kaldi/src && \
        ./configure --shared --openblas-root=../tools/OpenBLAS/install && \
        sed -i "s/\-g # -O0 -DKALDI_PARANOID.*$/-O3 -DNDEBUG/" kaldi.mk && \
        make depend -j4 && \
        make -j4 && \
        cd /kaldi/tools && \
        ./extras/install_irstlm.sh && \
        wget https://github.com/denizyuret/nlpcourse/raw/master/download/srilm-1.7.0.tgz -O srilm.tgz && \
        ./extras/install_srilm.sh && \
        rm -f *.tgz *.tar.gz *.tar.bz2

# clone, install and test abkhazia
WORKDIR /abkhazia
RUN git clone https://github.com/bootphon/abkhazia.git . && \
        KALDI_PATH=/kaldi ./configure && \
        python setup.py build && \
        python setup.py install
