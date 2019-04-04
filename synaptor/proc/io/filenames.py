""" File storage conventions """

# Segment info files
seginfo_dirname = "seg_infos"
seginfo_fmtstr = "seg_info_{tag}.df"
merged_seginfo_fname = "merged_cleft_info.df"
merged_seginfo_fmtstr = "merged_cleft_info_{tag}.df"

# Segment continuations
contin_dirname = "continuations"
contin_fmtstr = "continuations_{chunk_tag}_{face_tag}.h5"


# Segmentation merging id maps
idmap_dirname = "id_maps"
idmap_fmtstr = "id_map_{tag}.df"


# Duplicate connection merging id map
dup_map_fname = "dup_id_map.df"


# Edge info files
edgeinfo_dirname = "chunk_edges"
edgeinfo_fmtstr = "chunk_edges_{tag}.df"
merged_edgeinfo_fname = "merged_edges.df"
final_edgeinfo_fname = "final_edgelist.df"
tagged_final_edgeinfo_fname = "final_edgelist_{}.df"


# Overlap matrices
overlaps_dirname = "overlaps"
overlaps_fmtstr = "chunk_overlap_{tag}.df"
max_overlaps_fname = "max_overlaps.df"


# PyTorch network
network_dirname = "network"
network_fname = "net.py"
network_chkpt = "net.chkpt"

# Task time durations
timing_dirname = "task_durations"
timing_fmtstr = "{tag}"
