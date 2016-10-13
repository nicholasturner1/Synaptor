#!/usr/bin/env julia

#config.jl
#-------------------------------
# Runtime-specific parameters for input data

#Pathname to synapse and semantic output
# nothing indicates use of semantic_arr
network_output_filename = nothing;

#Pathname to segmentation volume
# currently assumed to be an HDF5 file
segmentation_filename = "dummy.sgm.h5";
#dataset path name within file
seg_dset_name = "/main";

output_prefix = "demo";

#Whether to read entire datasets
# into RAM
sem_incore = false;
seg_incore = false;

#If the segmentation data is offset
# from the network output, put the
# (1-indexed) coordinate of the start
# of the segmentation here
seg_start = [22657,18049,4003];

#Shape of output segmentation if desired
output_seg_shape = [2048,2048,256];

#If using ooc processing, specify the bounds of the volume
# which you'd like to analyze
# (in relative coordinates to the start of the segmentation)
scan_start_coord = [1,1,1];
scan_end_coord = [2048,2048,256];
