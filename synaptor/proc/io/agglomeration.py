import os
import itertools
import subprocess

import numpy as np
import fastremap
import zstandard

from ...types.bbox import BBox3d, Vec3d
from ...types.bbox import chunking
from ... import io


DCMP = zstandard.ZstdDecompressor()


def readchunk(cvpath, bbox, startcoord, chunksize, scratchpath,
              voxelres=0, layer=1, bits_per_dim=10, maxmip=11,
              correctvers=True):
    ws = io.read_cloud_volume_chunk(cvpath, bbox, mip=voxelres)

    chunks, chunkinds = reqdchunks(bbox, Vec3d(startcoord), Vec3d(chunksize))
    for (chunk, xyz) in zip(chunks, chunkinds):
        chunk = chunk.translate(-bbox._min)
        remapchunk(ws, chunk, xyz, scratchpath, layer=layer,
                   bits_per_dim=bits_per_dim, maxmip=maxmip,
                   correctvers=correctvers)

    return ws


def reqdchunks(bbox, startcoord, chunksize):
    end = bbox._max - startcoord
    start = bbox._min - startcoord
    xbounds = chunking.bounds1D(end[0], chunksize[0], start[0])
    ybounds = chunking.bounds1D(end[1], chunksize[1], start[1])
    zbounds = chunking.bounds1D(end[2], chunksize[2], start[2])

    chunks = [BBox3d(x, y, z).translate(startcoord) for (x, y, z)
              in itertools.product(xbounds, ybounds, zbounds)]

    chunkinds = [(bbox._min-startcoord) // chunksize
                 for bbox in chunks]

    return chunks, chunkinds


def remapchunk(seg, chunk, chunkindex, scratchpath,
               layer=1, bits_per_dim=10, maxmip=11, correctvers=True):
    x, y, z = chunkindex
    pcgchunkid = io.pcg.get_chunk_id(
                     layer=layer, x=x, y=y, z=z,
                     bits_per_dim=bits_per_dim)

    data = seg[chunk.index()]

    try:
        if correctvers:
            mappings = readremapfiles(scratchpath, chunkindex,
                                      pcgchunkid, maxmip=maxmip)
        else:
            mappings = _readremapfiles(scratchpath, chunkindex,
                                       pcgchunkid, maxmip=maxmip)
    except subprocess.CalledProcessError as e:
        if data.max() == 0:
            return data
        else:
            raise e

    for mapping in mappings:
        data = fastremap.remap(data, mapping, in_place=False,
                               preserve_missing_labels=True)

    seg[chunk.index()] = data

    return seg


def readremapfiles(scratchpath, chunkindex, pcgchunkid, maxmip=11):
    mipinds = indsbymip(chunkindex, maxmip)
    remotefiles = [os.path.join(
                      scratchpath, "agg/remap",
                      f"done_{mip}_{formatcoord(index)}_{pcgchunkid}.data.zst")
                   for (mip, index) in enumerate(mipinds)]

    localfiles = sortmapfiles(io.pull_files(remotefiles))

    return [readzstdmapping(f) for f in localfiles]


def _readremapfiles(scratchpath, chunkindex, pcgchunkid, maxmip=11):
    """Keeping the wrong version for testing"""
    mipinds = indsbymip(chunkindex, maxmip)
    remotefiles = [os.path.join(
                      scratchpath, "agg/remap",
                      f"done_{mip}_{formatcoord(index)}_{pcgchunkid}.data.zst")
                   for (mip, index) in enumerate(mipinds)]

    # BUG - 1 -> 10 -> 2 -> ...
    localfiles = sorted(io.pull_files(remotefiles))

    return [readzstdmapping(f) for f in localfiles]


def sortmapfiles(filenames):
    sortedfiles = [None] * len(filenames)

    for f in filenames:
        index = int(f.split('_')[1])
        assert sortedfiles[index] is None, "multiple files at the same MIP"
        sortedfiles[index] = f

    return sortedfiles


def indsbymip(baseindex, maxmip):
    inds = list()
    for i in range(maxmip):
        inds.append((baseindex[0] // 2 ** i,
                     baseindex[1] // 2 ** i,
                     baseindex[2] // 2 ** i))

    return inds


def formatcoord(chunkindex):
    return f"{chunkindex[0]}_{chunkindex[1]}_{chunkindex[2]}"


def readzstdmapping(filename, dtype=np.uint64):
    with open(filename, 'rb') as f:
        content = f.read()

    decompressed = DCMP.decompress(content)
    ids = np.frombuffer(decompressed, dtype=dtype)
    assert len(ids) % 2 == 0

    return {ids[i*2]: ids[i*2+1] for i in range(len(ids) // 2)}


def readhotfixfiles(bbox, scratchpath, chunksize, startcoord, mip=11,
                    layer=1, bits_per_dim=10):
    chunks, chunkinds = reqdchunks(bbox, Vec3d(startcoord), Vec3d(chunksize))

    remotefiles = list()
    pcgids = list()
    for (chunk, ind) in zip(chunks, chunkinds):
        x, y, z = ind
        pcgids.append(io.pcg.get_chunk_id(
                          layer=layer, x=x, y=y, z=z,
                          bits_per_dim=bits_per_dim))

        mipind = indsbymip(ind, mip)[mip-1]

        remotefiles.append(
            os.path.join(
                scratchpath, "agg/remap",
                f"done_{mip-1}_{formatcoord(mipind)}_{pcgids[-1]}.data.zst"))

    matchedfiles = sortfilesbypcgid(pcgids, io.pull_files(remotefiles))
    mappings = [readzstdmapping(f) for f in matchedfiles]

    return chunks, mappings


def sortfilesbypcgid(pcgids, filenames):
    sortedfiles = list()
    for pcgid in pcgids:
        filtered = [f for f in filenames if str(pcgid) in f]
        assert len(filtered) == 1, ("more than one pcgid match:"
                                    " {pcgid} -> {filtered}")
        sortedfiles.append(filtered[0])

    return sortedfiles
