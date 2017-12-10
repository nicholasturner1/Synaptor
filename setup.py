#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name='synaptor',
    version='0.0.1',
    description='Processing voxelwise convnet output to predict synaptic clefts, and assigning synaptic partners using asynet',
    author='Nicholas Turner',
    author_email='nturner@cs.princeton.edu',
    url='https://github.com/nicholasturner1/Synaptor',
    packages=['synaptor',
              'synaptor.clefts',
              'synaptor.edges',
              'synaptor.merge',
              'synaptor.io']
)
