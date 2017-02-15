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

#Polygon mask filename
# Useful if your data doesn't fill the whole volume
# or significant output artifacts exist
#mask_poly_fname = "cons_bbox_shifted.csv";
mask_poly_fname = nothing;

#Segment "MST" fname
# Whether the segments within the volume need to be remapped
# by an MST-like datastructure
#seg_mst_fname = "/mnt/data01/s1/sgm.h5";
#seg_mst_thresh = 0.2;
seg_mst_fname = nothing;
seg_mst_thresh = nothing;

#=================================
#out-of-core parameters
=================================#
scan_chunk_shape = [1024,1024,128];

DEBUG = true;
