""" Image normalization procedure for Phase 3 of the IARPA MICrONS program """
import numpy as np


def normalize_chunk(img, histograms, z_offset,
                    lower_clip_frac=0.01, upper_clip_frac=0.01,
                    minval=1, maxval = np.iinfo(np.uint8).max,
                    copy=False):
    assert img.shape[2] == len(histograms), "mismatched inputs"

    normed = img if not copy else np.empty(img.shape, dtype=img.dtype)

    for z in range(img.shape[2]):
        normed[:, :, z] = normalize_slice(
                              img[:, :, z], histograms[z+z_offset],
                              lower_clip_frac, upper_clip_frac,
                              minval=minval, maxval=maxval)

    return normed


def normalize_slice(imgslice, histogram,
                    lower_clip_frac, upper_clip_frac,
                    minval=1, maxval=np.iinfo(np.uint8).max):
    lower, upper = find_clamping_values(
                       histogram, lower_clip_frac, upper_clip_frac)
    lookup = make_lookup_table(lower, upper, minval, maxval)

    return lookup[imgslice]


def find_clamping_values(histogram, lower_clip_frac, upper_clip_frac):
    """
    Find the histogram values that capture the lower and upper clip fraction
    """
    assert 0 <= lower_clip_frac <= 1, "invalid lower_clip_frac"
    assert 0 <= upper_clip_frac <= 1, "invalid upper_clip_frac"

    histogram[0] = 0

    total = histogram.sum()
    if total == 0:
        return 0, 0

    cdf = np.cumsum(histogram) / total
    lower = np.nonzero(cdf > lower_clip_frac)[0][0] - 1
    upper = np.nonzero(cdf > 1 - upper_clip_frac)[0][0] - 1

    return lower, upper


def make_lookup_table(lowerbnd, upperbnd, minval, maxval):
    """Create a lookup array to map a slice of data"""
    lookup = np.arange(0, 256, dtype=np.float32)
    lookup = (lookup - lowerbnd) / (upperbnd - lowerbnd) * maxval
    np.clip(lookup, minval, maxval, out=lookup)
    np.round(lookup, out=lookup)

    return lookup
 
