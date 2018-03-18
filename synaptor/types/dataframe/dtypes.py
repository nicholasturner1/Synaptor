#!/usr/bin/env python3


class DType(object):

    length = 0
    fields = []

    def merge(fields1, fields2):
        pass


class Centroid(DType):

    length = 3
    fields = ["centroid_x","centroid_y","centroid_z"]

    def merge(fields1, fields2):
        
        sz1 = fields1[Size.fields[0]]
        sz2 = fields2[Size.fields[0]]
        new_sz = sz1+sz2

        centroid = [ ((fields1[f]*sz1)+(fields2[f]*sz2))/new_sz
                     for f in Centroid.fields ]

        return list(zip(Centroid.fields, centroid))


class Size(DType):

    length = 1
    fields = ["size"]

    def merge(fields1, fields2):
        return [("size", fields1["size"]+fields2["size"])]


class BBox(DType):

    length = 6
    fields = ["bbox_bx","bbox_by","bbox_bz",
              "bbox_ex","bbox_ey","bbox_ez"]

    def merge(fields1, fields2):
        pass


class PresynSeg(DType):

    length = 1
    fields = ["presyn_segid"]

    def merge(fields1, fields2):
        pass


class PostsynSeg(DType):

    length = 1
    fields = ["postsyn_segid"]

    def merge(fields1, fields2):
        pass


class PresynWeight(DType):

    length = 1
    fields = ["presyn_weight"]

    def merge(fields1, fields2):
        pass


class PostsynWeight(DType):

    length = 1
    fields = ["postsyn_weight"]

    def merge(fields1, fields2):
        pass


class PresynLoc(DType):

    length = 3
    fields = ["presyn_loc_x","presyn_loc_y","presyn_loc_z"]

    def merge(fields1, fields2):
        pass


class PostsynLoc(DType):

    length = 3
    fields = ["postsyn_loc_x","postsyn_loc_y","postsyn_loc_z"]

    def merge(fields1, fields2):
        pass


class PresynCount(DType):

    length = 1
    fields = ["presyn_count"]

    def merge(fields1, fields2):
        pass


class PostsynCount(DType):

    length = 1
    fields = ["postsyn_count"]

    def merge(fields1, fields2):
        pass
