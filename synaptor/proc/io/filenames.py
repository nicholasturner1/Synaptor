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


# Edge info files for a single chunk
edgeinfo_dirname = "chunk_edges"
edgeinfo_fmtstr = "chunk_edges_{tag}.df"

# Edge info file merged across chunks
merged_edgeinfo_fname = "merged_edges.df"
# w/ duplicates removed
final_edgeinfo_fname = "final_edges.df"
# Final edge info
final_edgeinfo_fname = "final.df"
