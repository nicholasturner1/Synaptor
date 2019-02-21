import numpy as np

from ... import proc
from ... import seg_utils
from .. import overlap
from .. import score
from . import dataset


def score_w_params(preds, img, seg, lbl,
                   asynet, patchsz, cc_thresh, sz_thresh,
                   dist_thr=1000, voxel_res=[4,4,40], to_ignore=[]):

    ccs = proc.seg.connected_components(preds, cc_thresh)

    ccs, _ = merge_duplicate_clefts(asynet, patchsz, img, seg, ccs,
                                 dist_thr=dist_thr, voxel_res=voxel_res)

    ccs, _ = seg_utils.filter_segs_by_size(ccs, sz_thresh, copy=False)

    return overlap.score_overlaps(ccs, lbl, mode="conservative",
                                  to_ignore=to_ignore)


def tune_parameters(preds, img, seg, labels,
                    asynet, patchsz, sz_threshs,
                    voxel_beta=1.5, cleft_beta=1.5,
                    voxel_bins=None, dist_thr=1000,
                    voxel_res=[4,4,40], to_ignore=[]):

    cc_thresh, ccs = tune_cc_threshold(preds, labels, voxel_beta, voxel_bins)

    ccs, _ = merge_duplicate_clefts(asynet, patchsz,
                                    img, seg, ccs,
                                    dist_thr, voxel_res)

    sz_thresh, prec, rec = tune_sz_threshold(ccs, labels, cleft_beta,
                                             sz_threshs, to_ignore)

    return cc_thresh, sz_thresh, prec, rec


def tune_cc_threshold(preds, labels, voxel_beta=1.5, voxel_bins=None):

    if voxel_bins is None:
        voxel_bins = [0.01*i for i in range(101)]

    tps, fps, fns = analyze_thresholds(preds, labels, voxel_bins)

    cc_thresh = opt_threshold(tps, fps, fns, voxel_beta, voxel_bins)

    ccs = proc.seg.connected_components(preds, cc_thresh)

    return cc_thresh, ccs


def analyze_thresholds(preds, labels, voxel_bins=None):

    if voxel_bins is None:
        voxel_bins = [0.01*i for i in range(101)]

    positive_bins, _ = np.histogram(preds[labels != 0], bins=voxel_bins)
    negative_bins, _ = np.histogram(preds[labels == 0], bins=voxel_bins)

    tps = np.cumsum(positive_bins[::-1])[::-1]
    fps = np.cumsum(negative_bins[::-1])[::-1]
    fns = np.cumsum(positive_bins)

    return tps, fps, fns


def opt_threshold(tps, fps, fns, voxel_beta=1.5, voxel_bins=None):

    if voxel_bins is None:
        voxel_bins = [0.01*i for i in range(101)]

    assert len(tps)==len(fps)==len(fns)==(len(voxel_bins)-1), "length mismatch"

    old_err = np.seterr(invalid="ignore",divide="ignore")

    precs = tps / (tps + fps)
    recs = tps / (tps + fns)

    np.seterr(**old_err)

    opt_i = find_best_fscore(precs, recs, voxel_beta)


    return voxel_bins[opt_i+1]


def merge_duplicate_clefts(asynet, patchsz, img, seg, clf,
                           dist_thr=1000, voxel_res=[4,4,40]):

    edges = proc.edge.infer_edges(asynet, img, clf, seg, patchsz)

    full_info_df = proc.edge.add_cleft_locs(edges, clf)

    dup_id_map = proc.edge.merge.merge_duplicate_clefts(full_info_df, dist_thr,
                                                        voxel_res)

    return seg_utils.relabel_data(clf, dup_id_map), dup_id_map


def tune_sz_threshold(ccs, labels, beta, sz_threshs=None, to_ignore=[],
                      mode="conservative"):

    if sz_threshs is None:
        sz_threshs = [100*i for i in range(8)]

    sz_threshs = sorted(sz_threshs)

    ccs = np.copy(ccs)

    n_threshs = len(sz_threshs)
    precs, recs = zero_vec(n_threshs), zero_vec(n_threshs)
    n_preds, n_lbls = zero_vec(n_threshs), zero_vec(n_threshs)
    for (i,sz_thresh) in enumerate(sz_threshs):
        ccs, _ = seg_utils.filter_segs_by_size(ccs, sz_thresh, copy=False)

        prec, rec, npred, nl = overlap.score_overlaps(ccs, labels,
                                                      mode=mode,
                                                      to_ignore=to_ignore)

        precs[i], recs[i], n_preds[i], n_lbls[i] = prec[0], rec[0], npred, nl

    opt_i = find_best_fscore(precs, recs, beta)

    opt_thresh = sz_threshs[opt_i]
    prec = precs[opt_i]
    rec = recs[opt_i]

    return opt_thresh, prec, rec


def find_best_fscore(precs, recs, beta):
    old_settings = np.seterr(divide="ignore",invalid="ignore")
    opt_i = np.nanargmax(score.all_fscores_PR(precs, recs, beta))
    np.seterr(**old_settings)
    return opt_i


def zero_vec(length, dtype=np.float64):
    return np.zeros((length,), dtype=dtype)


def parse_datasets(*args):
    return (parse_dataset(arg) for arg in args)


def parse_dataset(arg):
    if isinstance(arg, dataset.EvalDataset):
        return arg
    elif arg is None:
        print("WARNING: empty dataset!")
        return None
    else:
        return dataset.EvalDataset(arg)


def read_dataset(dset):

    if not isinstance(dset, dataset.EvalDataset):
        dset = dataset.EvalDataset(dset)

    dset.read()

    return dset


def make_clefts_at_params(dset, cc_thresh=None, sz_thresh=None):

    dset = read_dataset(dset)

    if cc_thresh is not None:
        clefts = [proc.seg.connected_components(p, cc_thresh).astype('uint32')
                  for p in dset.preds]
    else:
        #assume preds are already thresholded
        clefts = dset.preds

    if sz_thresh is not None:
        clefts = [seg_utils.filter_segs_by_size(vol, sz_thresh)[0]
                  for vol in clefts]

    return clefts
