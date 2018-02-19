#!/usr/bin/env python3

from Cython.Build import cythonize
from setuptools import setup, find_packages, Extension

extensions = [
    Extension("synaptor.seg_utils._seg_utils", sources=["synaptor/seg_utils/_seg_utils.pyx"])
]

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
              'synaptor.io'],
    ext_modules = cythonize(extensions)
)
