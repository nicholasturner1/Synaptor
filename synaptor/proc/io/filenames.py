__doc__ = """
File storage conventions
"""

# Segment info files for a single chunk
seginfo_dirname = "seg_infos"
seginfo_fmtstr = "seg_info_{tag}.df"

# Segment info file merged across chunks
merged_seginfo_fname = "merged_cleft_info.df"


# Segment continuations for a chunk
contin_dirname = "continuations"
contin_fmtstr = "continuations_{tag}.h5"


# Segmentation merging id maps
idmap_dirname = "id_maps"
idmap_fmtstr = "id_map_{tag}.df"


# Edge info files for a single chunk
edgeinfo_dirname = "chunk_edges"
edgeinfo_fmtstr = "chunk_edges_{tag}.df"


# Duplicate connection merging id map
dup_map_fname = "dup_id_map.df"


# Edge info file merged across chunks
merged_edgeinfo_fname = "merged_edges.df"
# w/ duplicates removed
final_edgeinfo_fname = "final_edges.df"
# Final edge info
final_edgeinfo_fname = "final.df"


# Overlap matrices
overlaps_dirname = "overlaps"
overlaps_fmtstr = "chunk_overlap_{tag}.df"
max_overlaps_fname = "max_overlaps.df"


# PyTorch network
network_dirname = "network"
network_fname = "net.py"
network_chkpt = "net.chkpt"
