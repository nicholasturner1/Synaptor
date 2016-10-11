#!/usr/bin/env julia

#=
  Translation of a voxel file into a segmentation - create_seg_volume.jl
=#
module create_seg_volume

unshift!(LOAD_PATH,".")
import io_u
import chunk_u

#-----------------------------
include("parameters.jl")
include(ARGS[1])

voxel_filename = "$(output_prefix)_voxels.csv"
output_filename = "$(output_prefix)_seg.h5"
offset = seg_start - 1;

#seg_chunk_shape in params
#output_seg_shape in config
#-----------------------------


function main()


  println("Reading voxels")
  @time segment_voxels = io_u.read_voxel_file( voxel_filename, -offset )

  println("Creating Dataset")
  @time seg = io_u.create_seg_dset( output_filename, output_seg_shape,
                                    seg_chunk_shape, "/main" )


  bounds = chunk_u.chunk_bounds( output_seg_shape, seg_chunk_shape )


  println("Making chunk plans...")
  @time chunk_membership = deal_voxels_to_chunks( segment_voxels, bounds )


  chunk = zeros( seg_dtype, (seg_chunk_shape...) )


  num_chunks = length(bounds)
  for chunk_id in 1:num_chunks

    println("Writing chunk $chunk_id of $num_chunks...")

    fill_chunk_with_voxels!( chunk, chunk_membership[chunk_id],
                             bounds[chunk_id].first-1 )

    write_chunk_to_output( seg, chunk, bounds[chunk_id] )

  end

end


function deal_voxels_to_chunks( voxels, bounds )

  membership = Vector{Vector{Pair{Vector{Int},Int}}}(length(bounds))
  for i in eachindex(membership) membership[i] = [] end

  for (v,segid) in voxels
    for i in 1:length(bounds)

      if in_bounds(v,bounds[i])
        push!(membership[i],v=>segid)
        break
      end

    end
  end

  membership
end

function in_bounds( voxel, bounds )

  #BROADCASTING IS THE DEVIL
  # ( all(voxel .>= bounds.first) &&
  #   all(voxel .<= bounds.second)  )

  b_beg, b_end = bounds

  ( voxel[1] >= b_beg[1] &&
    voxel[2] >= b_beg[2] &&
    voxel[3] >= b_beg[3] &&

    voxel[1] <= b_end[1] &&
    voxel[2] <= b_end[2] &&
    voxel[3] <= b_end[3] )
end

function fill_chunk_with_voxels!( chunk, voxels, offset )

  fill!(chunk,eltype(chunk)(0));

  for (v,id) in voxels
    i,j,k = v - offset;
    chunk[i,j,k] = id;
  end

end

function write_chunk_to_output( output_dset, chunk, bounds )

  b_beg, b_end = bounds

  output_dset[b_beg[1]:b_end[1],
              b_beg[2]:b_end[2],
              b_beg[3]:b_end[3]] = chunk
end

main()

end #module
