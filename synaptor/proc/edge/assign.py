""" Assignment Methods from network output """


import operator
import itertools


IMPLEMENTED = ["max", "single thresh", "double thresh"]


def make_assignments(pre_scores, post_scores, thresh=0, thresh2=0,
                     assign_type="max"):
    """
    Each assignment function returns a list of assignments. Each assignment
    is a tuple of (presyn_segid, postsyn_segid, presyn_score, postsyn_score)
    """
    assert assign_type in IMPLEMENTED, (f"assign type {assign_type} "
                                        "not supported")

    if assign_type == "max":
        return assign_by_max(pre_scores, post_scores)

    elif assign_type == "single thresh":
        return assign_by_thresh(pre_scores, post_scores, thresh, thresh)

    elif assign_type == "double thresh":
        return assign_by_thresh(pre_scores, post_scores, thresh, thresh2)


def assign_by_max(pre_scores, post_scores):
    """
    Make a single edge assignment by the maximum score:

    Returns a list with a single tuple fitting the interface
      (presyn_segid, postsyn_segid, presyn_score, postsyn_score)
    """
    pre_seg, pre_score = max(pre_scores.items(), key=operator.itemgetter(1))
    post_seg, post_score = max(post_scores.items(), key=operator.itemgetter(1))

    return [(pre_seg, post_seg, pre_score, post_score)]


def assign_by_thresh(pre_scores, post_scores, pre_thresh, post_thresh):
    """
    """
    max_pre_seg, max_pre_score = max(pre_scores.items(),
                                     key=operator.itemgetter(1))
    if max_pre_score > pre_thresh:
        pre_segs, pre_scores = all_over_thresh(pre_scores.items(), pre_thresh)
    else:
        pre_segs, pre_scores = [max_pre_seg], [max_pre_score]

    post_segs, post_scores = all_over_thresh(post_scores.items(), post_thresh)

    result = list()
    for (i, j) in itertools.product(range(len(pre_segs)),
                                    range(len(post_segs))):
        result.append((pre_segs[i], post_segs[j],
                       pre_scores[i], post_scores[j]))

    return result


def all_over_thresh(weights, thresh):
    """ Finds all of the segments and weights over a threshold value """

    segs = list()
    wts = list()

    for (seg, wt) in weights:
        if wt > thresh:
            segs.append(seg)
            wts.append(wt)

    return segs, wts


def assign_all_by_thresh(all_scores, pre_thresh, post_thresh):
    """
    Generate edges by threshold scheme for multiple clefts. Each returned edge
    is a tuple of the form:

      (cleft_id, presyn_segid, postsyn_segid)
    """

    full_edges = list()

    for (cleft_id, cleft_weights) in all_scores.items():
        new_edges = assign_by_thresh(cleft_weights, pre_thresh, post_thresh)

        tagged_edges = [(cleft_id, edge[0], edge[1]) for edge in new_edges]
        full_edges += tagged_edges

    return full_edges


def assign_all(scores, assign_type="max", thresh=None, thresh2=None):

    full_edges = list()

    for (cleft_id, (pre, post)) in scores.items():
        new_edges = make_assignments(pre, post,
                                     assign_type=assign_type,
                                     thresh=thresh, thresh2=thresh2)

        tagged_edges = [(cleft_id, edge[0], edge[1]) for edge in new_edges]
        full_edges += tagged_edges

    return full_edges


if __name__ == "__main__":

    import unittest

    class AssignTests(unittest.TestCase):

        def test_assign_all(self):
            scores = {0: ({0: 0,  1: 1,  2: 0}, {0: 0,  1: 0,  2: 1}),
                      1: ({0: 0,  1: 0,  2: 1}, {0: 0,  1: 1,  2: 0})}

            max_res = [(0, 1, 2),  (1, 2, 1)]
            self.assertEqual(assign_all(scores), max_res)

            thresh2_res = []
            self.assertEqual(assign_all(scores, assign_type="single thresh",
                                        thresh=2),
                             thresh2_res)

    unittest.main()
