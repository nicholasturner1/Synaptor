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
#max_chunk_multiplier, size_div in params
#-----------------------------


function main()


  println("Reading voxels")
  @time segment_voxels = io_u.read_voxel_file( voxel_filename, -offset )

  println("Creating Dataset")
  @time seg = io_u.create_seg_dset( output_filename, output_seg_shape,
                                    seg_chunk_shape, "/main" )


  println("Making chunk plans...")
  @time membership, bounds = binary_deal_voxels_to_chunks( segment_voxels,
                              max_chunk_multiplier*seg_chunk_shape,
                              output_seg_shape, seg_chunk_shape, size_div )


  chunk = zeros( seg_dtype, (seg_chunk_shape...) )


  num_chunks = length(bounds)
  for chunk_id in 1:num_chunks

    println("Writing chunk $chunk_id of $num_chunks...")

    fill_chunk_with_voxels!( chunk, membership[chunk_id],
                             bounds[chunk_id].first-1 )

    write_chunk_to_output( seg, chunk, bounds[chunk_id] )

  end

end


"""

    deal_voxels_to_chunks( voxels, bounds )

  Splits a list of voxel coordinates into a list of lists depending upon which
  bound contains each voxel. Naive approach.
"""
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



"""

    binary_deal_voxels_to_chunks( voxels, initial_chunk_shape, volume_shape,
      final_chunk_shape, size_div )

  Splits a list of voxel coordinates into a list of lists depending upon which
  bound contains each voxel. Performs an initial deal to large initial chunks,
  and progressively deals voxels to contained smaller chunks until it reaches
  the final chunk shape. Chunk shape is divided by size_div in each round.
"""
function binary_deal_voxels_to_chunks( voxels, initial_chunk_shape,
  volume_shape, final_chunk_shape, size_div )

  chunk_shape = initial_chunk_shape

  println("Performing initial deal")
  bounds = chunk_u.chunk_bounds( volume_shape, chunk_shape )
  members = deal_voxels_to_chunks( voxels, bounds )

  while all( chunk_shape .> final_chunk_shape )

    chunk_shape = div(chunk_shape,size_div);
    println("Chunk shape: $chunk_shape")

    new_bounds = chunk_u.chunk_bounds( volume_shape, chunk_shape )
    members = deal_voxels_to_contained_chunks( members, bounds, new_bounds )
    bounds = new_bounds

  end

  members, bounds
end


"""

    deal_voxels_to_contained_chunks( memberships, L_bounds, S_bounds )

  Given an initial deal of voxels into large bounds (L_bounds), sort the voxels into
  smaller bounds (S_bounds), which are contained within the larger ones.
"""
function deal_voxels_to_contained_chunks( memberships, L_bounds, S_bounds)

  new_memberships = Vector{Vector{Pair{Vector{Int},Int}}}(length(S_bounds));
  for i in eachindex(new_memberships) new_memberships[i] = [] end

  for (i,members) in enumerate(memberships)

    #first pass to find which small bounds possibly contain
    # the voxels here
    contained_bounds = Vector{Int}();

    for (j,sb) in enumerate(S_bounds  )
      if !contained_within( sb, L_bounds[i] ) continue end
      push!(contained_bounds, j)
    end

    #second pass to deal the voxels within the larger bound
    for (v,segid) in members

      for j in contained_bounds
        if in_bounds(v,S_bounds[j])
          push!(new_memberships[j], v=>segid)
          break
        end
      end

    end

  end

  new_memberships
end


"""

    contained_within( bounds1, bounds2 )

  Determines whether a pair of bounds (bounds1 - specifying a volume)
  is completely contained within another (bounds2)
"""
function contained_within( bounds1, bounds2 )
  beg1,end1 = bounds1
  beg2,end2 = bounds2

  ( beg1[1] >= beg2[1] &&
    beg1[2] >= beg2[2] &&
    beg1[3] >= beg2[3] &&

    end1[1] <= end2[1] &&
    end1[2] <= end2[2] &&
    end1[3] <= end2[3] )
end

"""
Not currently using these... but could be useful if I get lazy later
"""
function lte3d( v1, v2 )
  ( v1[1] <= v2[1] &&
    v1[2] <= v2[2] &&
    v1[3] <= v2[3] )
end

function gte3d( v1, v2 )
  ( v1[1] >= v2[1] &&
    v1[2] >= v2[2] &&
    v1[3] >= v2[3] )
end


"""

    fill_chunk_with_voxels!( chunk, voxels, offset )

  Takes voxel mappings, and fills a chunk with them. Puts 0 into
  the chunk wherever a voxel does not specify a value.
"""
function fill_chunk_with_voxels!( chunk, voxels, offset )

  fill!(chunk,eltype(chunk)(0));

  for (v,id) in voxels
    i,j,k = v - offset;
    chunk[i,j,k] = id;
  end

end


"""

    write_chunk_to_output( output_dset, chunk, bounds )

  Sends a chunk of values to a region of a dataset determined
  by the bounds. No error checking currently performed to ensure
  bounds specify a proper volume size
"""
function write_chunk_to_output( output_dset, chunk, bounds )

  b_beg, b_end = bounds

  output_dset[b_beg[1]:b_end[1],
              b_beg[2]:b_end[2],
              b_beg[3]:b_end[3]] = chunk
end

main()

end #module
