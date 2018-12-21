__doc__ = """
Segmentation Utility Functions

A set of common functions for working with 3d segmentation volumes.

These functions include:
- Centroid coordinates (centers_of_mass)
- Bounding boxes (bounding_boxes)
- Segment sizes (segment_sizes)
- General data relabeling (relabel_data)
- Relabeling segment ids to 1:N (relabel_data_1N)
- Finding nonzero unique ids (nonzero_unique_ids)
- High-pass size thresholding (filter_segs_by_size)
- General segment removal (filter_segs_by_id)
- Computing overlap sizes (count_overlaps)
- Splitting segments by overlap with a base (split_by_overlap)
- Down/Upsampling over the last 2 dimensions (upsample2d, downsample_seg)
- Dilation over the last 2 dimensions (dilate_by_k)

Other functions exist. See the documentation for each function (and submodules)
for more information.

Nicholas Turner <nturner@cs.princeton.edu>, 2017-8
"""
from . import describe
from .describe import *

from . import filtering
from .filtering import *

from . import overlap
from .overlap import *

from . import relabel
from .relabel import *

from . import resample
from .resample import *

from . import misc
from .misc import *
