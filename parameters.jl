#!/usr/bin/env julia

#parameters.jl
#-------------------------------
#parameters for input data

vol_map = Dict(
  "boundary" => 1,
  "axon"     => 2,
  "dendrite" => 3,
  "non-PSD"  => 4,
  "PSD"      => 5
)

cc_thresh = 0.35
size_thresh = 200
dilation_param = 15

sem_dtype = Float32
seg_dtype = UInt32

#out-of-core parameters
w_radius = [300,300,30];
scan_chunk_shape = [500,500,300];
set_size_hint = 15000;
