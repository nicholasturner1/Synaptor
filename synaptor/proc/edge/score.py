""" Scoring Methods from network output """


IMPLEMENTED = ["avg", "sum", "sum mix", "size mix", "pre size mix"]


def compute_scores(wt_avgs, wt_sums, seg_szs, alpha=1,
                   pre_type=None, post_type=None, score_type="avg"):
    """
    """

    pre_type = score_type if pre_type is None else pre_type
    post_type = score_type if post_type is None else post_type

    pre_avgs, post_avgs = split_values(wt_avgs)
    pre_sums, post_sums = split_values(wt_sums)

    presyn_scores = compute_side_scores(pre_avgs, pre_sums, seg_szs,
                                        score_type=pre_type, alpha=alpha)
    postsyn_scores = compute_side_scores(post_avgs, post_sums, seg_szs,
                                         score_type=post_type, alpha=alpha)

    return presyn_scores, postsyn_scores


def compute_side_scores(avgs, sums, sizes, score_type="avg", alpha=1):
    """
    """

    assert score_type in IMPLEMENTED, f"score type {score_type} not supported"

    if score_type == "avg":
        return avgs

    elif score_type == "sum":
        return sums

    elif score_type == "sum_mix":
        return mix_scores(avgs, sums, alpha)

    elif score_type == "size mix":
        sizes = normalize(sizes)
        return mix_scores(avgs, sizes, alpha)


def split_values(values_dict):

    pre_values = dict()
    post_values = dict()

    for (k, v) in values_dict.items():
        pre, post = v
        pre_values[k] = pre
        post_values[k] = post

    return pre_values, post_values


def mix_scores(dict1, dict2, alpha):

    assert dict1.keys() == dict2.keys(), "mismatched dicts"

    scores = dict()

    for k in dict1.keys():
        v1 = dict1[k]
        v2 = dict2[k]

        scores[k] = alpha*v1 + (1-alpha)*v2

    return scores


def normalize(values_dict):
    value_sum = sum(values_dict.values())
    return {k: v/value_sum for (k, v) in values_dict.items()}


def compute_all(cid_avgs, cid_sums, cid_szs, alpha=1,
                pre_type=None, post_type=None, score_type="avg"):

    assert cid_avgs.keys() == cid_sums.keys(), "mismatched inputs"
    assert cid_avgs.keys() == cid_szs.keys(), "mismatched inputs"

    all_scores = dict()
    for cleft_id in cid_avgs.keys():
        avgs = cid_avgs[cleft_id]
        sums = cid_sums[cleft_id]
        szs = cid_szs[cleft_id]

        all_scores[cleft_id] = compute_scores(avgs, sums, szs, alpha=alpha,
                                              pre_type=pre_type,
                                              post_type=post_type,
                                              score_type=score_type)

    return all_scores


if __name__ == "__main__":

    import unittest

    class ScoreTests(unittest.TestCase):

        def test_split_values(self):
            d = {0: (0, 0), 1: (1, 1), 2: (2, 2)}
            res = ({0: 0,  1: 1,  2: 2}, {0: 0,  1: 1,  2: 2})
            self.assertEqual(split_values(d), res)

        def test_mix_scores(self):
            d1 = {0: 0,  1: 1,  2: 2}
            d2 = {0: 1,  1: 2,  2: 3}
            mix = {0: 0.5,  1: 1.5,  2: 2.5}
            self.assertEqual(mix_scores(d1, d2, 0.5), mix)
            self.assertEqual(mix_scores(d1, d2, 1), d1)
            self.assertEqual(mix_scores(d1, d2, 0), d2)

        def test_normalize(self):
            d = {0: 1,  1: 2,  2: 1}
            res = {0: 1/4,  1: 2/4,  2: 1/4}
            self.assertEqual(normalize(d), res)

        def test_compute_all(self):
            avgs = {0: {0: (0, 0),  1: (1, 0),  2: (0, 1)},
                    1: {0: (0, 0),  1: (0, 1),  2: (1, 0)}}
            sums = {0: {0: (0, 0),  1: (2, 0),  2: (0, 3)},
                    1: {0: (0, 0),  1: (0, 2),  2: (3, 0)}}
            szs = {0: {0: 10,  1: 2,  2: 3},
                   1: {0: 10,  1: 2,  2: 3}}

            avg_res = {0: ({0: 0,  1: 1,  2: 0}, {0: 0,  1: 0,  2: 1}),
                       1: ({0: 0,  1: 0,  2: 1}, {0: 0,  1: 1,  2: 0})}
            self.assertEqual(compute_all(avgs, sums, szs), avg_res)
            # TODO: more tests here

    unittest.main()
