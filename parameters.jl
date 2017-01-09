#!/usr/bin/env julia

#parameters.jl
#-------------------------------
# relatively stable parameters for input data

#A name for each volume in the network output
vol_map = Dict(
  "boundary" => 1,
  "axon"     => 2,
  "dendrite" => 3,
  "non-PSD"  => 4,
  "PSD"      => 5
)

#Connected components threshold
cc_thresh = 0.35
#Size threshold
size_thresh = 200
#Dilation distance parameter
dilation_param = 15

#Datatypes of inputs&outputs
sem_dtype = Float32
seg_dtype = UInt32

#=================================
#out-of-core parameters
=================================#
#
w_radius = [300,300,30];
scan_chunk_shape = [1024,1024,256];
#Size hint for voxel set (mild performance tuning, not important)
set_size_hint = 15000;
#Median Filter Over Threshold Radius
mfot_radius = 3

#=================================
#create_seg_volume parameters
=================================#
#chunk size of input&output segmentation HDF5 files
seg_chunk_shape = [256,256,32];
#how much larger to make the initial chunk deal
max_chunk_multiplier = 8;
#how quickly to shrink the chunks after
# the initial deal
size_div = 8;
