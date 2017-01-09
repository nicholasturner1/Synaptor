#!/usr/bin/env julia
__precompile__()

#=
  General Utils - utils.jl
=#
module utils 

import seg_u

export find_synaptic_edges
export make_semantic_assignment, voxelwise_class_judgment
export convert_to_global_coords, coord_center_of_mass
export tuple_add


#-----------------------------------------------
# Synapse-specific utils
"""

    find_synaptic_edges( psd_segs, seg, semmap, size_thresh = 1e3,
                         axon_label = 3, dendrite_label = 4 )

  Determines the polarity and segment members of synapse segments by analyzing
  their overlap. Discards synapse candidates which only overlap with one cell segment,
  or those which overlap between two segments assigned to the same semantic category.
"""
function find_synaptic_edges( psd_segs, seg, semmap,
  axon_label = 2, dendrite_label = 3)

  if length(keys(semmap)) == 0 return Dict(), [], spzeros(0,0) end

  overlap = seg_u.count_overlapping_labels( psd_segs, seg, maximum(keys(semmap)) );

  seg_ids = extract_unique_rows(overlap)
  axons, dendrites = split_map_into_groups( semmap, [axon_label, dendrite_label] );
  axon_overlaps = overlap[:,axons]; dend_overlaps = overlap[:,dendrites];

  #debug
  # println("# axons: $(length(axons))")
  # println("# dendrites: $(length(dendrites))")

  if length(nonzeros(axon_overlaps)) == 0 || length(nonzeros(dend_overlaps)) == 0
    return Dict(), seg_ids, overlap
  end

  #finding the axons/dendrites with the highest overlap with the
  # psd segment
  #changing this implementation to avoid allocating huge arrays
  #axon_max, axon_ind  = findmax(axon_overlaps, 2);
  #dend_max, dend_ind  = findmax(dend_overlaps, 2);

  #axon_ind = ind2sub(size(axon_overlaps), axon_ind[:])[2];
  #dend_ind = ind2sub(size(dend_overlaps), dend_ind[:])[2];
  axon_max, axon_ids = find_max_overlaps( axon_overlaps, axons, seg_ids )
  dend_max, dend_ids = find_max_overlaps( dend_overlaps, dendrites, seg_ids )
  #println("$axon_max, $axon_ids")
  #println("$dend_max, $dend_ids")
  #println("$seg_ids")

  #only count edges if they overlap with SOME axon or dendrite
  valid_edges, invalid_edges = filter_edges( axon_max, dend_max );

  #edges as an array of Int tuples
  #[( axons[axon_ind[i]], dendrites[dend_ind[i]] ) for i in valid_edges], valid_edges

  edges = Dict( sid => (axon_ids[sid],dend_ids[sid]) for sid in valid_edges )

  edges, invalid_edges, overlap
end


"""

    extract_unique_rows(overlap)

  Finds the unique row ids with nonzero entries
"""
function extract_unique_rows(overlap)
  unique(findn(overlap)[1])
end

function find_max_overlaps( overlaps, col_ids, seg_ids )

  rs, cs = findn(overlaps); vs = nonzeros(overlaps)

  maxs = Dict( s => eltype(vs)(0) for s in seg_ids )
  inds = Dict( s => eltype(cs)(0) for s in seg_ids )

  for i in eachindex(rs)
    r = rs[i]; v = vs[i]

    if v > maxs[r] 
      maxs[r] = v
      inds[r] = col_ids[cs[i]]
    end
  end

  maxs, inds
end


"""

    split_map_into_groups( segmap, ids )

  Takes a mapping from segment ids to groups, and a list of groups.
  Separates the segment ids into lists depending upon their group membership,
  and ignores segments mapped to groups other than those listed in groups
"""
function split_map_into_groups( segmap::Dict, group_ids::Vector{Int} )

  groups = [ Vector{Int}() for i in group_ids ]

  for (k,v) in segmap
    for i in eachindex(group_ids)
      if v == group_ids[i] push!(groups[i], k) end
    end
  end

  groups
end


"""

    filter_edges( max_axon_overlap, max_dend_overlap )

  Performs filtering constraints on edges by means of semantic overlaps and
  synaptic segment size
"""
function filter_edges( max_axon_overlap, max_dend_overlap )

  num_psd_segs = length(max_axon_overlap)
  valid_edges = Vector{Int}();
  invalid_edges = Vector{Int}();

  zT = valtype(max_axon_overlap)(0)
  for k in keys(max_axon_overlap)
    if max_axon_overlap[k] == zT || max_dend_overlap[k] == zT
      push!(invalid_edges,k)
    else
      push!(valid_edges, k)
    end
  end

  valid_edges, invalid_edges
end


#-----------------------------------------------
# Semantic Inference utils

"""

    make_semantic_assignment( seg, sem_probs, classes )

  Takes a segmentation, a pixelwise probability map over several classes,
  and indices of the possible assignment classes. Assigns each segment in the
  segmentation (aside from 0) to one of the assignment classes by comparing
  the sum probability over each voxel for each candidate class.
"""
function make_semantic_assignment( seg, sem_probs, classes::Array{Int}, 
  weights::Dict{Int,Vector{Float64}}=Dict{Int,Vector{Float64}}() )

  class_index = Dict{Int,Int}( classes[i] => i for i in eachindex(classes) );

  #segid => array : weight of each class
  #if weights == nothing weights = Dict{Int,Vector{Float64}}() end
  num_classes = length(classes);

  #accumulating weight for each segment
  for k in classes
    class_k = class_index[k]
    for z in 1:size(seg,3)
      for y in 1:size(seg,2)
        for x in 1:size(seg,1)

          segid = seg[x,y,z];
          if segid == eltype(seg)(0) continue end

          if !haskey(weights, segid)  weights[ segid ] = zeros((num_classes,)) end

          weights[ segid ][ class_k ] += sem_probs[x,y,z,k];

        end
      end
    end
  end

  #making assignments by max weight
  #index 2 selects index of max (instead of value)
  Dict{Int,Int}( k => classes[ findmax(weights[k])[2] ] for k in keys(weights) ), weights
end


"""

    voxelwise_class_judgment( d, classes )

 Takes a 4D volume of class probs, and makes a decision between the class indices
 supplied as arguments (e.g. axon vs. dendrite). Not really used anymore
"""
function voxelwise_class_judgment( d, classes )

  x,y,z,t = size(d);
  view = d[:,:,:,classes];

  maxval, maxind = findmax(view,4);

  judgments = reshape( ind2sub( size(view), maxind[:] )[4], (x,y,z) );

  for i in eachindex(judgments)
    judgments[i] = classes[judgments[i]];
  end

  judgments
end


#-----------------------------------------------
# Coordinate handling utils


"""

    coord_center_of_mass( coord_array )

  Returns the center of mass of the 3D locations within
  the passed iterable
"""
function coord_center_of_mass( coord_array )

  center_of_mass = [0,0,0]

  for coord in coord_array
    center_of_mass[1] += coord[1]
    center_of_mass[2] += coord[2]
    center_of_mass[3] += coord[3]
  end

  center_of_mass = round(Int,center_of_mass ./ length(coord_array));
  (center_of_mass[1],center_of_mass[2],center_of_mass[3])
end


"""

    convert_to_global_coords( coords, offset )

  Adds an offset to each coordinate within an iterable
"""
function convert_to_global_coords( coords, offset )
  [
    tuple_add( voxel_index, offset )
    for voxel_index in coords
  ]
end


#-----------------------------------------------
# Other utils

function tuple_add( t::Tuple, a )
  (t[1]+a[1],t[2]+a[2],t[3]+a[3])
end

end#module
