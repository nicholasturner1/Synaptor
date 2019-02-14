__doc__ = """
Column Schema for Database Tables and Dataframes
"""

# NOTE: All coordinate types should be XYZ ordered

cleft_id = "cleft_segid"

centroid_x = "centroid_x"
centroid_y = "centroid_y"
centroid_z = "centroid_z"
centroid_cols = [centroid_x, centroid_y, centroid_z]

bbox_bx = "bbox_bx"
bbox_by = "bbox_by"
bbox_bz = "bbox_bz"
bbox_ex = "bbox_ex"
bbox_ey = "bbox_ey"
bbox_ez = "bbox_ez"
bbox_cols = [bbox_bx, bbox_by, bbox_bz,
             bbox_ez, bbox_ey, bbox_ez]

# Size of a segment
size = "size"

# ====================================================
# Synapse assignment descriptors

presyn_id = "presyn_segid"
postsyn_id = "postsyn_segid"

presyn_x = "presyn_x"
presyn_y = "presyn_y"
presyn_z = "presyn_z"
postsyn_x = "postsyn_x"
postsyn_y = "postsyn_y"
postsyn_z = "postsyn_z"
presyn_coord_cols = [presyn_x, presyn_y, presyn_z]
postsyn_coord_cols = [postsyn_x, postsyn_y, postsyn_z]

# Average output weight for the current assignment
presyn_wt = "presyn_wt"
postsyn_wt = "postsyn_wt"

# num voxels used to make an assignment
presyn_sz = "presyn_sz"
postsyn_sz = "postsyn_sz"

# Watershed ID which maps to the assigned segment
presyn_basin = "presyn_basin"
postsyn_basin = "postsyn_basin"
