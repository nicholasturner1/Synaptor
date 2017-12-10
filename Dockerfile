FROM pytorch/pytorch


RUN apt-get update

# For igraph C backend
#https://github.com/igraph/python-igraph/blob/master/docker/minimal/Dockerfile
RUN apt-get install build-essential libxml2-dev zlib1g-dev -y
RUN apt-get install pkg-config libffi-dev libcairo-dev -y

#Fixes a conda bug - https://github.com/conda/conda/issues/6030
RUN conda update python

#For some reason, pip works for h5py and pandas, and conda doesn't
RUN pip install h5py pandas cloud-volume python-igraph

RUN git clone https://github.com/nicholasturner1/Synaptor.git

RUN pip install -e /workspace/Synaptor

WORKDIR /workspace/Synaptor/tasks
CMD ./dispatcher.sh 
