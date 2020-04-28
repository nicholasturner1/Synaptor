""" Synapse Assignment by Attentional Voxel Association Networks """
import time

import numpy as np
import torch
import scipy.ndimage as ndimage
import pandas as pd

from ...types import bbox
from ... import seg_utils
from .. import colnames as cn
from . import locs
from . import score
from . import assign


RECORD_SCHEMA = [cn.seg_id, cn.presyn_id, cn.postsyn_id,
                 *cn.presyn_coord_cols, *cn.postsyn_coord_cols,
                 cn.presyn_wt, cn.postsyn_wt,
                 cn.presyn_sz, cn.postsyn_sz]
SCHEMA_W_ROOTS = RECORD_SCHEMA + [cn.presyn_basin, cn.postsyn_basin]


def infer_edges(net, img, clf, seg, patchsz, batchsz,
                offset=(0, 0, 0), dil_param=5):

    cleft_ids = seg_utils.nonzero_unique_ids(clf)

    
    loader = make_data_loader(img, clf, seg, patchsz,
                              cleft_ids=cleft_ids,
                              batchsz=batchsz)
    dilkernel = make_dilation_kernel(dil_param)

    edges = list()  # list of eventual dataframe rows (as dicts)
    for sample in loader:
        # Most of these parts are GPU-based, so it's helpful
        # to group them into batches
        # b_{} => "batch_{}"
        b_cleft_ids = sample["cleft_id"]
        b_offsets = sample["offset"]
        b_segids = find_close_segments(sample, dilkernel)
        b_weights, b_sizes = infer_patch_weights(net, sample, b_segids)
        b_locs = extract_locs(sample, b_segids, offset)

        for i in range(len(b_cleft_ids)):
            cleft_id = b_cleft_ids[i]
            weights = b_weights[i]
            sizes = b_sizes[i]
            locs = b_locs[i]

            edges.append(make_assignment(cleft_id, weights, sizes, locs))

    return make_record_dframe(edges)


def make_data_loader(img, clf, seg, patchsz, cleft_ids=None, batchsz=1):
    # needs to be in sample
    # img, clf, seg, box_offset, cleft_id
    dataset = AVANDataset(img, clf, seg, patchsz, cleft_ids=cleft_ids)

    return torch.utils.data.DataLoader(dataset, batch_size=batchsz,
                                       collate_fn=custom_collate,
                                       num_workers=1, pin_memory=True)


class AVANDataset(torch.utils.data.Dataset):
    def __init__(self, img, clf, seg, patchsz, cleft_ids=None):
        super(AVANDataset, self).__init__()

        if cleft_ids is None:
            cleft_ids = seg_utils.nonzero_unique_ids(clf)

        # hard-coded as 1 loc per cleft for now
        cleft_locs = list(locs.pick_cleft_locs(
                              clf, cleft_ids, "centroid", 1, patchsz).items())

        self.img = img
        self.clf = clf
        self.seg = seg
        self.patchsz = patchsz
        self.locs = cleft_locs

    def __getitem__(self, i):
        cleft_id, cleft_locs = self.locs[i]
        # hard-coded as 1 loc per cleft for now
        assert len(cleft_locs) == 1, "only one loc impl for now"

        box = bbox.containing_box(cleft_locs[0], self.patchsz, self.clf.shape)
        offset = box.min()

        img_p, clf_p, seg_p = self.get_patches(cleft_id, box)

        return [cleft_id, offset, img_p, clf_p, seg_p]
        
    def get_patches(self, cleft_id, box):
        """ Return 5d patches specified by the box for pytorch """
        img_p = self.img[box.index()] / np.float32(255.)
        clf_p = (self.clf[box.index()] == cleft_id).astype("float32")
        seg_p = self.seg[box.index()]

        img_p = self._format_patch(img_p)
        clf_p = self._format_patch(clf_p)
        seg_p = self._format_patch(seg_p)

        return img_p, clf_p, seg_p

    def _format_patch(self, patch):
        return patch.transpose((2, 1, 0))[np.newaxis, np.newaxis, ...]

    def __len__(self):
        return len(self.locs)


def custom_collate(batch):
    # Current layout (from above):
    #  cleft_id, offset, img_p, clf_p, seg_p
    batch = list(zip(*batch))
    default_collate = torch.utils.data._utils.collate.default_collate

    img = [torch.as_tensor(elem) for elem in batch[2]]
    clf = [torch.as_tensor(elem) for elem in batch[3]]
    
    sample = dict(cleft_id=batch[0],
                  offset=batch[1],
                  img=torch.cat(img, 0),
                  clf=torch.cat(clf, 0),
                  seg=np.concatenate(batch[4], axis=0)
                  )

    return sample


def make_dilation_kernel(dil_param):
    kernel = ndimage.generate_binary_structure(2, 1)
    kernel = ndimage.iterate_structure(kernel, dil_param)

    kernel = np.stack((kernel, kernel, kernel), axis=0)

    width = kernel.shape[-1]
    return kernel.reshape((1, 1, 3, width, width))


def find_close_segments(sample, dilkernel):
    dilated_masks = torch_dilation(sample["clf"], dilkernel)

    segids = list()
    for i in range(len(sample["cleft_id"])):
        masks = dilated_masks[i, ...]
        seg = sample["seg"][i, ...]
        segids.append(seg_utils.nonzero_unique_ids(seg[masks]))

    return segids


def infer_patch_weights(net, sample, b_segids):
    #start = time.time()
    inference = infer_patch(net, sample)
    #print(f"actual inference in {time.time() - start:3f}s")

    #start = time.time()
    b_weights, b_sizes = [], []
    for i in range(len(sample["cleft_id"])):
        net_output = inference[i, ...]
        seg = sample["seg"][i, ...]
        segids = b_segids[i]

        new_weights, new_sizes = seg_weights(net_output, seg, segids)
        b_weights.append(new_weights)
        b_sizes.append(new_sizes)
    #print(f"seg weights in {time.time() - start:3f}s")

    return b_weights, b_sizes


def infer_patch(net, sample):
    with torch.no_grad():
        net_input = to_tensor(
                        torch.cat((sample["img"], sample["clf"]), axis=1))
        output = torch.sigmoid(net(net_input)[0])

    return output


def seg_weights(net_output, seg, segids=None):
    if segids is None:
        segids = seg_utils.nonzero_unique_ids(seg)

    weights, sizes = {}, {}
    presyn_output = net_output[0, ...]
    postsyn_output = net_output[1, ...]

    for i in segids:
        seg_mask = to_tensor((seg == i).astype("bool")[0, ...])
        sizes[i] = torch.sum(seg_mask).item()

        pre_wt = torch.sum(presyn_output[seg_mask]).item()
        post_wt = torch.sum(postsyn_output[seg_mask]).item()

        weights[i] = (pre_wt, post_wt)

    return weights, sizes


def make_assignment(cleft_id, weights, sizes, locs):

    averages = compute_averages(weights, sizes)
    pre_scores, post_scores = score.compute_scores(averages, weights, sizes)
    assignments = assign.make_assignments(pre_scores, post_scores)

    # Should only be a single assignment at the moment
    assert len(assignments) == 1, "multiple assignments made by max?"
    pre_seg, post_seg, pre_w, post_w = assignments[0]

    pre_loc, post_loc = locs[pre_seg], locs[post_seg]
    pre_sz, post_sz = sizes[pre_seg], sizes[post_seg]

    return make_record(cleft_id, pre_seg, post_seg,
                       pre_loc, post_loc, pre_w, post_w,
                       pre_sz, post_sz)


def compute_averages(weights, sizes):
    assert weights.keys() == sizes.keys()
    return {k: (weights[k][0]/sizes[k], weights[k][1]/sizes[k])
            for k in weights.keys()}


def make_record(cleft_id,
                pre_seg, post_seg,
                pre_loc, post_loc,
                pre_weight, post_weight,
                pre_size, post_size,
                pre_basin=None, post_basin=None):

    data = [cleft_id,         pre_seg,      post_seg,
            pre_loc[0],       pre_loc[1],   pre_loc[2],
            post_loc[0],      post_loc[1],  post_loc[2],
            pre_weight,       post_weight,
            pre_size,         post_size]

    assert len(data) == len(RECORD_SCHEMA), "mismatched data and schema"

    if pre_basin is None:
        return dict(zip(RECORD_SCHEMA, data))

    else:
        assert post_basin is not None, "pre but no post basin"
        data += [pre_basin, post_basin]
        return dict(zip(SCHEMA_W_ROOTS, data))


def make_record_dframe(record_list, record_basins=False):

    if len(record_list) == 0:
        if record_basins:
            return pd.DataFrame({k: {} for k in SCHEMA_W_ROOTS})
        else:
            return pd.DataFrame({k: [] for k in RECORD_SCHEMA})
    else:
        df = pd.DataFrame.from_records(record_list)
        if record_basins:
            return df[SCHEMA_W_ROOTS]
        else:
            return df[RECORD_SCHEMA]
    pass


def extract_locs(sample, segids=None, offset=(0, 0, 0)):
    # stub
    b_locs = list()
    for i in range(len(sample["cleft_id"])):
        b_locs.append({s: (0, 0, 0) for s in segids[i]})

    return b_locs


def to_tensor(npndarray, dtype=None):
    return torch.as_tensor(npndarray, dtype=dtype).cuda()


def torch_dilation(seg, kernel):

    with torch.no_grad():
        seg_t = to_tensor(seg)
        ker_t = to_tensor(kernel, torch.float32)
        sz = kernel.shape
        padding = (sz[2]//2, sz[3]//2, sz[4]//2)

        output = torch.nn.functional.conv3d(seg_t, ker_t, padding=padding)

    return output.data.cpu().numpy().astype("bool")
