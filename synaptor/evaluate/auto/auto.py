import numpy as np

from ... import proc
from ... import seg_utils
from ... import io
from .. import overlap

from . import toolbox as tb


def auto_eval(train_set, val_set, test_set=None,
              asynet=None, patchsz=(160, 160, 18), dist_thr=1000,
              voxel_res=[4, 4, 40], merge_ccs=True,
              output_prefix=None, write=False, delete=True,
              voxel_beta=1.5, cleft_beta=1.5,
              voxel_bins=None, sz_threshs=None):

    train_set = tb.parse_dataset(train_set)
    val_set = tb.parse_dataset(val_set)
    test_set = tb.parse_dataset(test_set)

    val_set.read()
    print("Tuning parameters on the validation set...")
    cc_thr, sz_thr, _, _, ccs = tune_parameters_dset(
                                    val_set, asynet, patchsz,
                                    voxel_beta, cleft_beta,
                                    thresh_ccs=True, voxel_bins=voxel_bins,
                                    sz_threshs=sz_threshs, dist_thr=dist_thr,
                                    voxel_res=voxel_res, merge_ccs=merge_ccs)

    print("Optimized thresholds: CC {}; Size {}".format(cc_thr, sz_thr))
    val_prec, val_rec, val_precs, val_recs = score_ccs_dset(val_set, ccs)
    print("Validation Set: {0:.3f}P/{1:.3f}R".format(val_prec, val_rec))
    print("Set-Wise:")
    print_setwise_scores(val_precs, val_recs)

    if delete:
        val_set.delete()

    if write:
        print("Making final ccs for validation set...")
        write_dset_ccs(ccs, output_prefix, "val")

    print("Scoring Training Set...")
    train_set.read()
    (tr_prec, tr_rec, tr_precs, tr_recs), ccs = score_w_params(
                                                    train_set, cc_thr, sz_thr,
                                                    asynet=asynet,
                                                    patchsz=patchsz,
                                                    merge_ccs=merge_ccs)

    print("Training Set: {0:.3f}P/{1:.3f}R".format(tr_prec, tr_rec))
    print("Set-Wise:")
    print_setwise_scores(tr_precs, tr_recs)

    if delete:
        train_set.delete()

    if write:
        print("Writing clefts...")
        write_dset_ccs(ccs, output_prefix, "train")

    if test_set is not None:
        print("Scoring Test Set...")
        test_set.read()
        (te_prec, te_rec, te_precs, te_recs), ccs = score_w_params(
                                                        test_set, cc_thr,
                                                        sz_thr, asynet=asynet,
                                                        patchsz=patchsz,
                                                        merge_ccs=merge_ccs)
        print("Test Set: {0:.3f}P/{1:.3f}R".format(te_prec, te_rec))
        print("Set-Wise:")
        print_setwise_scores(te_precs, te_recs)

        if delete:
            test_set.delete()

        if write:
            print("Writing clefts...")
            write_dset_ccs(ccs, output_prefix, "test")


def print_setwise_scores(precs, recs):
    for (i, (p, r)) in enumerate(list(zip(precs, recs))):
        print("Set {i}".format(i=i))
        print("Prec: {p}".format(p=p))
        print("Rec: {r}".format(r=r))


def tune_parameters_dset(dset, asynet, patchsz,
                         voxel_beta, cleft_beta, thresh_ccs=False,
                         voxel_bins=None, sz_threshs=None,
                         dist_thr=1000, voxel_res=[4, 4, 40],
                         merge_ccs=True):

    dset = tb.read_dataset(dset)

    print("Tuning Connected Components threshold...")
    ccs, cc_thresh = tune_cc_threshold_dset(dset, voxel_beta, voxel_bins)
    ccs = [cc.astype("uint32") for cc in ccs]

    if merge_ccs:
        assert asynet is not None
        print("Merging duplicates...")
        ccs, _ = merge_duplicate_clefts_dset(asynet, patchsz, dset,
                                             ccs, dist_thr, voxel_res)

    print("Tuning size threshold...")
    sz_thresh, prec, rec, ccs = tune_sz_threshold_dset(dset, ccs, cleft_beta,
                                                       sz_threshs,
                                                       thresh_ccs=thresh_ccs)

    return cc_thresh, sz_thresh, prec, rec, ccs


def score_w_params(dset, cc_thresh, sz_thresh,
                   asynet=None, patchsz=None, dist_thr=1000,
                   voxel_res=[4, 4, 40], merge_ccs=True,
                   mode="conservative"):

    dset = tb.read_dataset(dset)

    ccs = make_ccs_dset(dset, cc_thresh)
    ccs = [cc.astype("uint32") for cc in ccs]

    if merge_ccs:
        assert asynet is not None
        ccs, _ = merge_duplicate_clefts_dset(asynet, patchsz, dset,
                                             ccs, dist_thr, voxel_res)

    ccs = [seg_utils.filter_segs_by_size(cc, sz_thresh, copy=False)[0]
           for cc in ccs]

    return score_ccs_dset(dset, ccs, mode=mode), ccs


def score_ccs_dset(dset, ccs, mode="conservative"):

    dset = tb.read_dataset(dset)

    prec, rec, npreds, nlbls = 0., 0., 0, 0
    precs, recs = [], []  # single-vol records
    for (cc, lbl, to_ig) in zip(ccs, dset.labels, dset.to_ignore):
        p, r, npred, nlbl = overlap.score_overlaps(cc, lbl,
                                                   mode="conservative",
                                                   to_ignore=to_ig)

        old_tp = prec*npreds

        npreds += npred
        nlbls += nlbl

        prec = (old_tp + p[0]*npred) / npreds if npreds != 0 else 1
        rec = (old_tp + r[0]*nlbl) / nlbls if nlbls != 0 else 1

        precs.append(p)
        recs.append(r)

    return prec, rec, precs, recs


def tune_cc_threshold_dset(dset, voxel_beta=1.5, voxel_bins=None):

    dset = tb.read_dataset(dset)

    if voxel_bins is None:
        voxel_bins = [0.01*i for i in range(101)]

    tps, fps, fns = analyze_thresholds_dset(dset, voxel_bins)

    cc_thresh = tb.opt_threshold(tps, fps, fns, voxel_beta, voxel_bins)

    ccs = make_ccs_dset(dset, cc_thresh)

    return ccs, cc_thresh


def analyze_thresholds_dset(dset, voxel_bins=None):

    dset = tb.read_dataset(dset)

    if voxel_bins is None:
        voxel_bins = [0.01*i for i in range(101)]

    tps = np.zeros((len(voxel_bins)-1,))
    fps = np.zeros((len(voxel_bins)-1,))
    fns = np.zeros((len(voxel_bins)-1,))

    for (p, l) in zip(dset.preds, dset.labels):
        new_tps, new_fps, new_fns = tb.analyze_thresholds(p, l, voxel_bins)

        tps += new_tps
        fps += new_fps
        fns += new_fns

    return tps, fps, fns


def make_ccs_dset(dset, cc_thresh):
    dset = tb.read_dataset(dset)

    clfs = [proc.seg.connected_components(pred, cc_thresh)
            for pred in dset.preds]

    return clfs


def merge_duplicate_clefts_dset(asynet, patchsz, dset, ccs,
                                dist_thr=1000, voxel_res=[4, 4, 40]):

    dset = tb.read_dataset(dset)

    if not isinstance(ccs, list):
        ccs = [ccs]
    assert len(dset) == len(ccs), "mismatched ccs and dset"

    dup_maps = []
    merged_ccs = []
    for (img, seg, clf) in zip(dset.images, dset.segs, ccs):
        new_ccs, new_dup_map = tb.merge_duplicate_clefts(asynet, patchsz,
                                                         img, seg, clf,
                                                         dist_thr, voxel_res)

        dup_maps.append(new_dup_map)
        merged_ccs.append(new_ccs)

    return merged_ccs, dup_maps


def tune_sz_threshold_dset(dset, ccs, beta=1.5,
                           sz_threshs=None, thresh_ccs=False):

    dset = tb.read_dataset(dset)

    if not isinstance(ccs, list):
        ccs = [ccs]
    assert len(dset) == len(ccs), "mismatched ccs and dset"

    if sz_threshs is None:
        sz_threshs = [100*i for i in range(8)]

    sz_threshs = sorted(sz_threshs)
    ccs_c = [np.copy(cc) for cc in ccs]

    n_threshs = len(sz_threshs)
    precs, recs = tb.zero_vec(n_threshs), tb.zero_vec(n_threshs)
    n_preds, n_lbls = tb.zero_vec(n_threshs), tb.zero_vec(n_threshs)
    for (i, sz_thresh) in enumerate(sz_threshs):
        for (cc, lbl, to_ig) in zip(ccs_c, dset.labels, dset.to_ignore):

            cc, _ = seg_utils.filter_segs_by_size(cc, sz_thresh, copy=False)

            prec, rec, npred, nlbl = overlap.score_overlaps(
                                         cc, lbl, mode="conservative",
                                         to_ignore=to_ig)

            # This is a scheme to make sure we don't fall into
            # inconsistency
            #
            # rounding is useful for float precision
            old_tp = round(n_preds[i] * precs[i], 3)
            old_tp2 = round(n_lbls[i] * recs[i], 3)
            assert old_tp == old_tp2, "tps don't match for some reason"

            n_preds[i] += npred
            n_lbls[i] += nlbl

            if n_preds[i] != 0:
                precs[i] = (old_tp + prec[0]*npred) / n_preds[i]
            else:
                precs[i] = 1

            if n_lbls[i] != 0:
                recs[i] = (old_tp2 + rec[0]*nlbl) / n_lbls[i]
            else:
                recs[i] = 1

    opt_i = tb.find_best_fscore(precs, recs, beta)

    sz_thresh = sz_threshs[opt_i]
    prec = precs[opt_i]
    rec = recs[opt_i]

    if(thresh_ccs):
        ccs = [seg_utils.filter_segs_by_size(cc, sz_thresh)[0] for cc in ccs]

    return sz_thresh, prec, rec, ccs


def write_dset_ccs(ccs, output_prefix, tag):

    assert output_prefix is not None, "Need output_prefix"

    for (i, cc) in enumerate(ccs):
        fname = f"{output_prefix}_{tag}{i}.h5"

        print("Writing {}...".format(fname))
        # EvalDataset convention is to transpose inputs
        io.write_h5(cc.transpose((2, 1, 0)), fname)
