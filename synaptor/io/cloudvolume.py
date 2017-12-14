#!/usr/bin/env python3

import numpy as np
import cloudvolume #external package


from ..bbox import BBox3d


def read_cloud_volume_chunk(cv_name, bbox):

    cv.fill_missing = True #ensuring that we always read something
    cv = cloudvolume.CloudVolume(cv_name)

    return cv[bbox.index()][:,:,:,0]


def write_cloud_volume_chunk(data, cv_name, bbox):

    cv = cloudvolume.CloudVolume(cv_name)

    cv[bbox.index()] = data.astype(cv.dtype)


def create_seg_volume(cv_name, resolution, vol_size,
                      description, owners, offset=(0,0,0),
                      sources = None):

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
