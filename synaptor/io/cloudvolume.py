#!/usr/bin/env python3

import cloudvolume 
from ..bbox import BBox3d


def read_cloud_volume_chunk(cv_name, bbox):
    
    cv = cloudvolume.CloudVolume(cv_name)

    return cv[bbox.index()]


def write_cloud_volume_chunk(data, cv_name, bbox):

    cv = cloudvolume.CloudVolume(cv_name)

    cv[bbox.index()] = data


def create_seg_volume(cv_name, resolution, vol_size, offset=(0,0,0)):

    info = cloudvolume.CloudVolume.create_new_info(1, "segmentation", np.uint32,
                                                   "raw", resolution, offset, 
                                                   vol_size

    cv = cloudVolume.CloudVolume(cv_name, mip=0, info=info)
    cv.commit_info()

    return cv
