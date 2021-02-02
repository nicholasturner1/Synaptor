"""IO for sampled section histograms"""
import json

import numpy as np

from ... import io


def read_histogram_bbox(cloudpath, bbox, mip=1):
    zmin, zmax = bbox.min()[2], bbox.max()[2]
    return read_histogram_range(cloudpath, zmin, zmax, mip=mip)


def read_histogram_range(cloudpath, zmin, zmax, mip=1, nonefill=True):

    remote_paths = [f"{cloudpath}/{mip}/{z}" for z in range(zmin, zmax)]

    local_paths = io.pull_files(remote_paths, check=False)

    histograms = dict()
    for (z, filename) in zip(range(zmin, zmax), local_paths):
        histograms[z] = _read_hist_from_json(filename, nonefill=nonefill)

    if any(hist is None for hist in histograms.values()):
        print("WARNING: some normalization files not found")

    return histograms


def read_histogram(cloudpath, z, mip=1, nonefill=True):
    remote_path = f"{cloudpath}/{mip}/{z}"

    local_path = io.pull_file(remote_path)
    return _read_hist_from_json(local_path, nonefill=nonefill)


def _read_hist_from_json(filename, nonefill=True):
    try:
        with open(filename) as f:
            data = json.load(f)
            return np.array(data["levels"], dtype=np.uint64)
    except FileNotFoundError as e:
        if nonefill:
            return None
        else:
            raise e
