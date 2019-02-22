""" General purpose ROC curve functions """

import operator
from collections import Counter

import numpy as np


def precision(preds, labels, penalize_dups=True):
    """
    Returns the precision score between two iterables of items, as well as
    a list of bools indicating which items in preds were counted as false
    positives. The second list is assumed to be the "ground truth" version.

    If penalize_dups is false, will collapse preds to its unique values.
    The false positive vector can be interpreted by comparing to these unique
    values (i.e. call np.unique(preds) yourself, and compare)
    """

    preds = preds if penalize_dups else np.unique(preds)

    if len(preds) == 0:
        return (1,[])

    fps = false_positives(preds, labels)
    num_tps = len(fps) - sum(fps)

    return num_tps / len(preds), list(fps)


def recall(preds, labels):
    """
    Returns the recall score between two iterables of items, as well as
    a vector of bools indicating which items in labels were counted as false
    negatives.
    """

    if len(labels) == 0:
        return (1,[])

    fns = false_negatives(preds, labels)
    num_tps = len(fns) - sum(fns)

    return num_tps / len(fns), list(fns)


def fscore(preds, labels, beta, penalize_dups=True):
    """
    Returns the F-score between two iterables of items, as well as
    a two lists of bools indicating which items in preds were counted as
    false positives & negatives in labels.

    If penalize_dups is false, will collapse preds to its unique values.
    The false positive vector can be interpreted by comparing to these unique
    values (i.e. call np.unique(preds) yourself, and compare).
    """

    preds = preds if penalize_dups else np.unique(preds)

    fps = false_positives(preds, labels)
    fns = false_negatives(preds, labels)

    num_fps, num_fns = sum(fps), sum(fns)
    num_tps = len(labels) - num_fns

    return single_fscore(num_tps, num_fps, num_fns, beta), fps, fns


def single_fscore(tp, fp, fn, beta):
    """ Computes a single F-score given all the required values """

    betasq = beta ** 2

    return (1 + betasq) * tp / ((1 + betasq) * tp + betasq * fn + fp)


def f1score(preds, labels, penalize_dups=True):
    """ Shortcut for fscore """
    return fscore(preds, labels, 1., penalize_dups)


def single_f1score(tp, fp, fn):
    """ Shortcut for single_fscore """
    return single_fscore(tp,fp,fn,1.)


def single_fscore_PR(prec, rec, beta):
    """ Computes an F-score from a precision and recall score """

    betasq = beta ** 2

    if prec == 0. or rec == 0.:
        return 0.

    return (1+betasq) / (1./prec + betasq/rec)


def all_fscores_PR(precs, recs, beta):
    """
    Computes the fscore values for every prec and rec value in
    np.arrays
    """

    fscores = np.zeros(precs.shape)

    for i in np.ndindex(precs.shape):
        fscores[i] = single_fscore_PR(precs[i], recs[i], beta)

    return fscores


def false_positives(preds, labels):
    """
    Identifies the false positives between two lists of iterables
    """

    label_counts = Counter(labels)

    fps = [False] * len(preds)
    for (i,p) in enumerate(preds):

        if label_counts[p] > 0:
            label_counts[p] -= 1
        else:
            fps[i] = True

    return fps


def false_negatives(preds, labels):
    """
    Identifies the false negatives between two lists of iterables
    """
    return false_positives(labels, preds)


def prec_rec_curve2d_inclusive(points, labels, beta=1.):

    assert len(points) == len(labels), "mismatched inputs"

    first_axis, first_inds = np.unique(list(map(operator.itemgetter(0), points)),
                                       return_inverse=True)
    second_axis, second_inds = np.unique(list(map(operator.itemgetter(1), points)),
                                         return_inverse=True)

    pos_grid = np.zeros((first_axis.size,second_axis.size), dtype=np.uint32)
    neg_grid = np.zeros((first_axis.size,second_axis.size), dtype=np.uint32)

    for (i,j,lbl) in zip(first_inds, second_inds, labels):
        if lbl:
            pos_grid[i,j] += 1
        else:
            neg_grid[i,j] += 1

    fn = false_negative_grid_incl(pos_grid)
    tp = np.sum(pos_grid) - fn
    fp = np.sum(neg_grid) - false_negative_grid_incl(neg_grid)

    prec = tp / (tp + fp)
    rec = tp / (tp + fn)
    fscore = all_fscores_PR(prec, rec, beta)

    return prec, rec, fscore, first_axis, second_axis


def prec_rec_curve2d(points, labels, beta=1.):

    assert len(points) == len(labels), "mismatched inputs"

    first_axis, first_inds = np.unique(list(map(operator.itemgetter(0), points)),
                                       return_inverse=True)
    second_axis, second_inds = np.unique(list(map(operator.itemgetter(1), points)),
                                         return_inverse=True)

    pos_grid = np.zeros((first_axis.size,second_axis.size), dtype=np.uint32)
    neg_grid = np.zeros((first_axis.size,second_axis.size), dtype=np.uint32)

    for (i,j,lbl) in zip(first_inds, second_inds, labels):
        if lbl:
            pos_grid[i,j] += 1
        else:
            neg_grid[i,j] += 1

    tp = np.cumsum(np.cumsum(pos_grid[::-1,::-1],axis=0),axis=1)[::-1,::-1]

    fp = np.cumsum(np.cumsum(neg_grid[::-1,::-1],axis=0),axis=1)[::-1,::-1]

    #something ugly for now - need to move on
    #fn = false_negative_grid(pos_grid)
    fn = np.sum(pos_grid) - tp#false_negative_grid(pos_grid)

    prec = tp / (tp + fp)
    rec = tp / (tp + fn)
    fscore = all_fscores_PR(prec, rec, beta)

    return prec, rec, fscore, first_axis, second_axis
    # return tp, fp, fn


def false_negative_grid_excl(pos_grid):

    fn = np.zeros(pos_grid.shape, dtype=np.uint32)
    temp = np.zeros(pos_grid.shape, dtype=np.uint32)
    for (i,j) in zip(*np.nonzero(pos_grid)):

        temp[i+1:,:] = 1
        temp[:,j+1:] = 1
        fn += temp * pos_grid[i,j]
        temp[:] = 0

    return fn


def false_negative_grid_incl(pos_grid):

    fn = np.zeros(pos_grid.shape, dtype=np.uint32)
    for (i,j) in np.ndindex(fn.shape):
        fn[i,j] = np.sum(pos_grid[:i,:j])

    return fn


def iso_fcurve(fscore, recalls=None, beta=1):

    if recalls is None:
        recalls = np.linspace(0.01, 1, 100)

    betasq = beta ** 2

    precs = fscore*recalls / ((1 + betasq) * recalls - betasq * fscore)

    return recalls[precs >= 0], precs[precs >= 0]
