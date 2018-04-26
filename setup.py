#!/usr/bin/env python3

import numpy as np
from Cython.Build import cythonize
from setuptools import setup, find_packages, Extension

extensions = [
    Extension("synaptor.seg_utils._seg_utils", 
              sources=["synaptor/seg_utils/_seg_utils.pyx"],
              include_dirs=[np.get_include()])
]

setup(
    name='synaptor',
    version='0.0.1',
    description='Processing voxelwise convnet output to predict synaptic clefts, and assigning synaptic partners using asynet',
    author='Nicholas Turner',
    author_email='nturner@cs.princeton.edu',
    url='https://github.com/nicholasturner1/Synaptor',
    packages=['synaptor',
              'synaptor.evaluate',
              'synaptor.io',
              'synaptor.io.backends',
              'synaptor.proc_tasks',
              'synaptor.proc_tasks.chunk_ccs',
              'synaptor.proc_tasks.chunk_edges',
              'synaptor.proc_tasks.chunk_overlaps',
              'synaptor.proc_tasks.io',
              'synaptor.proc_tasks.merge_ccs',
              'synaptor.proc_tasks.merge_edges',
              'synaptor.proc_tasks.merge_overlaps',
              'synaptor.seg_utils',
              'synaptor.types',
              'synaptor.types.bbox',
              ],
    ext_modules = cythonize(extensions)
)
