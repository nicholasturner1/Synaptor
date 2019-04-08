FROM nvidia/cuda:10.0-cudnn7-devel-ubuntu18.04 


#Setting up ENV
RUN echo "deb http://developer.download.nvidia.com/compute/machine-learning/repos/ubuntu1804/x86_64 /" > /etc/apt/sources.list.d/nvidia-ml.list

ENV PYTHON_VERSION=3.6
ENV PATH /opt/conda/bin:$PATH


RUN apt-get update && \
    pytorchDeps='build-essential cmake git vim ca-certificates libjpeg-dev libpng-dev' && \
    igraphDeps='libxml2-dev zlib1g-dev pkg-config libffi-dev libcairo-dev' && \
    condaDeps='wget bzip2 libglib2.0-0 libxext6 libsm6 libxrender1 mercurial subversion' && \
    apt-get install -y --no-install-recommends $pytorchDeps $igraphDeps $condaDeps && \
    # for gsutil below
    apt-get install -y python-pip && \
    rm -rf /var/lib/apt/lists/* && \
#Install miniconda3
    echo 'export PATH=/opt/conda/bin:$PATH' > /etc/profile.d/conda.sh && \
    wget --quiet https://repo.continuum.io/miniconda/Miniconda3-4.5.12-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
#Python Dependencies
#For some reason, pip works for h5py and pandas, and conda doesn't
    pip --no-cache-dir install h5py pandas cloud-volume task-queue python-igraph future && \
    pip --no-cache-dir install requests psycopg2-binary && \
    conda install scipy pybind11 sqlalchemy && \
    conda install pytorch==1.0.1 torchvision cudatoolkit=10.0 -c pytorch && \
    # gsutil requires python2
    /usr/bin/pip --no-cache-dir install gsutil && \
    git clone https://github.com/nicholasturner1/Synaptor.git && \
    pip install -e /Synaptor && \
    conda clean -t -p


WORKDIR /Synaptor/tasks
