#!/usr/bin/env julia

#config.jl
#-------------------------------
# runtime-specific parameters for input data

#nothing indicates use of semantic_arr
network_output_filename = nothing
output_prefix = "config_test"
segmentation_filename = "../IARPA_draft/demo_chunk/chunk_22657-24704_18049-20096_4003-4258.sgm.h5"
seg_dset_name = "/main"

sem_incore = false
seg_incore = false

seg_start = [22657,18049,4003];

#relative coordinates to the start of the segmentation
scan_start_coord = [1,1,1]
scan_end_coord = [2048,2048,256]
