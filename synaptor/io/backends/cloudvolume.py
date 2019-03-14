""" CloudVolume Interface """

import cloudvolume


def read_cloud_volume_chunk(cv_name, bbox, mip=0, parallel=1, progress=False):
    """ Read a chunk of data specified by a bounding box. """

    cv = cloudvolume.CloudVolume(cv_name, mip=mip, parallel=parallel,
                                 progress=progress)

    # ensuring that we always read something
    # (i.e. that we know what we're doing)
    cv.fill_missing = True
    cv.bounded = False

    return cv[bbox.index()][:, :, :, 0]


def write_cloud_volume_chunk(data, cv_name, bbox, mip=0,
                             parallel=1, non_aligned=False, progress=False):
    """ Write a chunk of data specified by a bounding box. """

    cv = cloudvolume.CloudVolume(cv_name, mip=mip, parallel=parallel,
                                 non_aligned_writes=non_aligned,
                                 progress=progress)

    # ensuring that we always read something for non-aligned writes
    cv.fill_missing = True
    cv.bounded = False

    cv[bbox.index()] = data.astype(cv.dtype)


def init_seg_volume(cv_name, resolution, vol_size,
                    description, owners, offset=(0, 0, 0),
                    sources=None, chunk_size=(64, 64, 64)):
    """ Initialize a CloudVolume for use as a cleft segmentation. """

    info = cloudvolume.CloudVolume.create_new_info(1, "segmentation", "uint32",
                                                   "raw", resolution, offset,
                                                   vol_size,
                                                   chunk_size=chunk_size)

    cv = cloudvolume.CloudVolume(cv_name, mip=0, info=info)

    cv.provenance["owners"] = owners
    cv.provenance["description"] = description

    if sources is not None:
        cv.provenance["sources"] = sources

    cv.commit_info()
    cv.commit_provenance()

    return cv
