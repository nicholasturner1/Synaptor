#!/usr/bin/env python3
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()


__doc__ = """
CloudVolume Interface

Nicholas Turner <nturner@cs.princeton.edu>, 2018
"""


import numpy as np
import cloudvolume #external package


from ...bbox import BBox3d


def read_cloud_volume_chunk(cv_name, bbox):
    """ Reads a chunk of data specified by a bounding box """

    cv = cloudvolume.CloudVolume(cv_name)

    #ensuring that we always read something
    cv.fill_missing = True 
    cv.bounded = False 

    return cv[bbox.index()][:,:,:,0]


def write_cloud_volume_chunk(data, cv_name, bbox):
    """ Writes a chunk of data specified by a bounding box """

    cv = cloudvolume.CloudVolume(cv_name)

    cv[bbox.index()] = data.astype(cv.dtype)


def init_seg_volume(cv_name, resolution, vol_size,
                    description, owners, offset=(0,0,0),
                    sources = None):
    """ Initializes a CloudVolume for use as a cleft segmentation """

    info = cloudvolume.CloudVolume.create_new_info(1, "segmentation", "uint32",
                                                   "raw", resolution, offset,
                                                   vol_size)

    cv = cloudvolume.CloudVolume(cv_name, mip=0, info=info)


    cv.provenance["owners"] = owners
    cv.provenance["description"] = description

    if sources is not None:
        cv.provenance["sources"] = sources


    cv.commit_info()
    cv.commit_provenance()

    return cv
