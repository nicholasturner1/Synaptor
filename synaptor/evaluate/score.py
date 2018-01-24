#!/usr/bin/env python3


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
