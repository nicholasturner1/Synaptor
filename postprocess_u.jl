#!/usr/bin/env julia
__precompile__()


module postprocess_u

export centers_of_mass
export make_semantic_assignment
export edge_list_precision_recall
export dilate_by_k, manhattan_distance2D
export segment_sizes, filter_segments_by_size!
export connected_components3D, count_overlapping_labels
export get_inspection_window
export synapse_location_precision_recall



"""

    segment_sizes( seg )

  Returns a mapping from segment id to the size of each segment
"""
function segment_sizes{T}( seg::Array{T} )

  counts = Dict{T,Int}();

  z = zero(T)
  for i in eachindex(seg)
    if seg[i] == z continue end

    counts[seg[i]] = get(counts, seg[i], 0) + 1
  end

  counts
end


"""

    count_overlapping_labels( d, labels )

  Returns an overlap matrix between the two passed segmentations.
"""
function count_overlapping_labels( d, labels, max_label=nothing )

  #ignoring zero segment
  maxd = round(Int,maximum(d)); maxl = round(Int,maximum(labels));

  if max_label == nothing
    counts = spzeros(Int, maxd, maxl);
  else
    counts = spzeros(Int, maxd, max_label);
  end

  for i in eachindex(d)

    val = d[i]
    lab = labels[i]

    if val == eltype(d)(0) continue end
    if lab == eltype(labels)(0) continue end

    counts[ val, lab ] += 1

  end

  counts
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

    filter_edges( max_axon_overlap, max_dend_overlap, psd_sizes, size_thresh )

  Performs filtering constraints on edges by means of semantic overlaps and
  synaptic segment size
"""
function filter_edges( max_axon_overlap, max_dend_overlap, psd_sizes, size_thresh )

  num_psd_segs = length(max_axon_overlap)
  valid_edges = Vector{Int}();
  for i in 1:num_psd_segs
    if max_axon_overlap[i] == 0 continue end
    if max_dend_overlap[i] == 0 continue end
    if psd_sizes[i] <= size_thresh continue end

    push!(valid_edges, i)
  end

  valid_edges
end


"""

    find_synaptic_edges( psd_segs, seg, semmap, size_thresh = 1e3,
                         axon_label = 3, dendrite_label = 4 )

  Determines the polarity and segment members of synapse segments by analyzing
  their overlap. Discards synapse candidates which only overlap with one cell segment,
  or those which overlap between two segments assigned to the same semantic category.
"""
function find_synaptic_edges( psd_segs, seg, semmap, size_thresh = 1e3,
  axon_label = 2, dendrite_label = 3, size_filter=true)

  overlap = count_overlapping_labels( psd_segs, seg, maximum(keys(semmap)) );

  axons, dendrites = split_map_into_groups( semmap, [axon_label, dendrite_label] );
  axon_overlaps = overlap[:,axons]; dend_overlaps = overlap[:,dendrites];

  #debug
  # println("# axons: $(length(axons))")
  # println("# dendrites: $(length(dendrites))")

  if length(nonzeros(axon_overlaps)) == 0 || length(nonzeros(dend_overlaps)) == 0
    return [(0,0)], []
  end

  #finding the axons/dendrites with the highest overlap with the
  # psd segment
  axon_max, axon_ind  = findmax(axon_overlaps, 2);
  dend_max, dend_ind  = findmax(dend_overlaps, 2);

  axon_ind = ind2sub(size(axon_overlaps), axon_ind[:])[2];
  dend_ind = ind2sub(size(dend_overlaps), dend_ind[:])[2];

  #only count edges if they overlap with SOME axon or dendrite
  psd_sizes = segment_sizes( psd_segs );
  valid_edges = filter_edges( axon_max, dend_max, psd_sizes, size_thresh );

  #edges as an array of Int tuples
  [( axons[axon_ind[i]], dendrites[dend_ind[i]] ) for i in valid_edges], valid_edges
end


"""

    edge_list_precision_recall( predicted_list, ground_truth_list )

  Computes precision and recall over two arrays of tuples
"""
function edge_list_precision_recall( pred_list, gt_list )

  TP = length( Set(intersect(pred_list, gt_list)) )
  FP = length( setdiff(pred_list, gt_list)   )
  FN = length( setdiff(gt_list, pred_list)   )

  prec = TP / (TP + FP); recall = TP / (TP + FN )

  (prec, recall)
end


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
Takes a 4D volume of class probs, and makes a decision between the class indices
 supplied as arguments (e.g. axon vs. dendrite). Not really used anymore
"""
function make_voxel_class_judgment( d, classes )

  x,y,z,t = size(d);
  view = d[:,:,:,classes];

  maxval, maxind = findmax(view,4);

  judgments = reshape( ind2sub( size(view), maxind[:] )[4], (x,y,z) );

  for i in eachindex(judgments)
    judgments[i] = classes[judgments[i]];
  end

  judgments
end


"""

    assign_component!( arr, masked, xstart, ystart, zstart, segid )

  Traverses the component connected to the start index, and assigns the
  values within the component to segid. Uses a depth first strategy.
"""
function assign_component!{T}(arr::Array{T}, masked::BitArray{3},
  xstart,ystart,zstart, segid)

  xmax, ymax, zmax = size(masked)
  to_explore = Tuple{Int,Int,Int}[(xstart, ystart, zstart)]
  explored   = Tuple{Int,Int,Int}[];
  #explored = Set{Tuple{Int,Int,Int}}();

  @inbounds while !isempty(to_explore)

    x,y,z = pop!(to_explore)
    push!(explored, (x,y,z))

    arr[x,y,z] = segid
    masked[x,y,z] = true

    if x > 1 && !masked[ x-1,  y, z ] push!( to_explore, (x-1,y,z) ) end
    if y > 1 && !masked[ x,  y-1, z ] push!( to_explore, (x,y-1,z) ) end
    if z > 1 && !masked[ x,  y, z-1 ] push!( to_explore, (x,y,z-1) ) end

    if x < xmax && !masked[ x+1, y, z ] push!( to_explore, (x+1,y,z) ) end
    if y < ymax && !masked[ x, y+1, z ] push!( to_explore, (x,y+1,z) ) end
    if z < zmax && !masked[ x, y, z+1 ] push!( to_explore, (x,y,z+1) ) end

  end

  Set(explored)
end


"""

    connected_components3D( d, thresh )

  Performs connected components over d using a high-pass threshold.
"""
function connected_components3D{T}( d::Array{T}, thresh=zero(T) )

  #true => don't connect me
  masked = d .<= T(thresh)
  res = zeros(Int, size(d));

  xmax, ymax, zmax = size(d)
  segid = zero(Int)

  for z in 1:zmax
    for y in 1:ymax
      for x in 1:xmax
        @inbounds if masked[x,y,z] continue end
        segid += 1
        assign_component!(res, masked,x,y,z, segid)
      end
    end
  end

  res
end


"""

    connected_component3D( d, sub, thresh=zero(T) )

  Fills out a single connected component seeded at the passed location
"""
function connected_component3D{T}( d::Array{T}, seed::Tuple{Int,Int,Int}, thresh=zero(T) )

  masked = d .<= T(thresh)

  component_vol = zeros(UInt8, size(d))
  x,y,z = seed

  component_voxels = assign_component!(component_vol, masked, x,y,z, 1)

  component_vol, component_voxels
end


function connected_component3D!{T}( d::Array{T}, seed::Tuple{Int,Int,Int}, vol::Array{UInt8}, masked::BitArray, thresh=zero(T) )

  for i in eachindex(d)
    masked[i] = d[i] <= T(thresh)
  end

  fill!(vol,zero(T))
  x,y,z = seed

  assign_component!( vol, masked, x,y,z, 1 )
end


function convert_to_global_coords( component_voxels, offset )
  [
    ( voxel_index[1] + offset[1],
      voxel_index[2] + offset[2],
      voxel_index[3] + offset[3])

    for voxel_index in component_voxels
  ]
end


"""

    manhattan_distance2D( d )

  Performs a 2D manhattan distance transformation over
  a 3D volume.
"""
function manhattan_distance2D!{T}( d::Array{T,3} )

  restype = UInt32
  maxx, maxy, maxz = size(d)
  dists = zeros(restype, size(d))

  for k in 1:maxz
    for j in 1:maxy
      for i in 1:maxx

        if  d[i,j,k] > T(0)
           dists[i,j,k] = 0
        else
           dists[i,j,k] = typemax(restype)
        end

        if i>1  &&  dists[i-1,j,k]+1 <= dists[i,j,k]
          dists[i,j,k] = dists[i-1,j,k]+1;
          d[i,j,k] = d[i-1,j,k];
        end
        if j>1  &&  dists[i,j-1,k]+1 <= dists[i,j,k]
          dists[i,j,k] = dists[i,j-1,k]+1;
          d[i,j,k] = d[i,j-1,k];
        end

        #for 3d case
        #if k>1  dists[i,j,k] = minimum(( dists[i,j,k], dists[i,j,k-1]+1 )) end

      end
    end
  end

  for k in maxz:-1:1
    for j in maxy:-1:1
      for i in maxx:-1:1

        if i<maxx  &&  dists[i+1,j,k]+1 <= dists[i,j,k]
          dists[i,j,k] = dists[i+1,j,k]+1;
          d[i,j,k] = d[i+1,j,k];
        end
        if j<maxy  &&  dists[i,j+1,k]+1 <= dists[i,j,k]
          dists[i,j,k] = dists[i,j+1,k]+1;
          d[i,j,k] = d[i,j+1,k];
        end
        #if k<maxz  dists[i,j,k] = minimum(( dists[i,j,k], dists[i,j,k+1]+1 )) end

      end
    end
  end

  dists 
end


"""

    dilate_by_k( d, k )

  Returns a copy of d with the segments within d dilated by k
  in 2D manhattan distance
"""
function dilate_by_k!( d, k )

  md = manhattan_distance2D!(d)

  for i in eachindex(d)
    if md[i] > k
      d[i] = eltype(d)(0)
    end
  end

end


"""

    filter_segments_by_size!( d, thresh )

  Traverses a volume, and removes segments less than or equal to
  the threshold value in size
"""
function filter_segments_by_size!( d, thresh )

  sizes = segment_sizes(d)

  to_keep = Vector{eltype(keys(sizes))}()

  for (segid,size) in sizes
    if size > thresh push!(to_keep, segid) end
  end

  for i in eachindex(d)
    if !(d[i] in to_keep)
      d[i] = eltype(d)(0)
    end
  end

end


"""

    centers_of_mass( seg )

  Finds the (rounded) center of mass coordinate for each segment within
  a segmentation volume
"""
function centers_of_mass( d )

  centers_of_mass = Dict{eltype(d),Vector}();
  sizes = Dict{eltype(d),Int}()

  maxx, maxy, maxz = size(d)
  for k in 1:maxz
    for j in 1:maxy
      for i in 1:maxx

        segid = d[i,j,k];
        if segid == 0 continue end

        centers_of_mass[segid] = get(centers_of_mass, segid, [0,0,0]) + [i,j,k];
        sizes[segid] = get(sizes, segid, 0) + 1;

      end
    end
  end

  for k in keys(centers_of_mass)
    centers_of_mass[k] = round(Int, centers_of_mass[k] / sizes[k] );
  end

  centers_of_mass
end


"""

    coord_center_of_mass
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
    get_inspection_window( dset, coord )
"""
function get_inspection_window( dset, coord, radius, bounds=nothing )

  coord = collect(coord) #translating from tuple to array

  beg_candidate = coord - radius;
  end_candidate = coord + radius;

  #limiting the indexing to specific bounds
  # (used for making matching volumes)
  if bounds != nothing
    beg_allowed = bounds.first
    end_allowed = bounds.second
  else
    beg_allowed = [1,1,1]
    end_allowed = [size(dset)...]
  end

  beg_i = max( beg_allowed, beg_candidate );
  end_i = min( end_allowed, end_candidate );

  #rel_coord = coord - beg_i;

  if length(size(dset)) == 3
    dset[
      beg_i[1]:end_i[1],
      beg_i[2]:end_i[2],
      beg_i[3]:end_i[3]], beg_i-1;
  elseif length(size(dset)) == 4
    dset[
      beg_i[1]:end_i[1],
      beg_i[2]:end_i[2],
      beg_i[3]:end_i[3],:], beg_i-1;
  end

  #return window, beg_i-1;
end


function fill_inspection_window!( window, dset, coord, radius, bounds=nothing )

  coord = collect(coord) #translating from tuple to array

  beg_candidate = coord - radius;
  end_candidate = coord + radius;

  #limiting the indexing to specific bounds
  # (used for making matching volumes)
  if bounds != nothing
    beg_allowed = bounds.first
    end_allowed = bounds.second
  else
    beg_allowed = [1,1,1]
    end_allowed = [size(dset)...]
  end

  beg_i = max( beg_allowed, beg_candidate );
  end_i = min( end_allowed, end_candidate );

  #rel_coord = coord - beg_i;
  window_size = end_i - beg_i + 1
  
  fill!( window, eltype(window)(0) )

  @inbounds window[
    1:window_size[1],
    1:window_size[2],
    1:window_size[3]
    ] = dset[
    beg_i[1]:end_i[1],
    beg_i[2]:end_i[2],
    beg_i[3]:end_i[3]];

  return beg_i-1;
end


function initialize_inspection_window( radius, dtype )
  zeros( dtype, (2*radius + 1)... )
end

function synapse_location_precision_recall( proposed_centers, gt_centers, thresh )

  num_prop = length(proposed_centers)
  num_gt   = length(gt_centers)

  distances = Array{Float64,Float64}( (num_prop, num_gt) )

  for j in 1:num_gt
    for i in 1:num_prop
      distances[i,j] = norm( (proposed_centers[i] - gt_centers[j]).^2 )
    end
  end

  min_distance_prop = minimum( distances, 2 )
  min_distance_gt   = minimum( distances, 1 )

  TPs_prop = sum( min_distance_prop .< thresh )
  TPs_gt   = sum( min_distance_gt   .< thresh )

  prec_liberal = TPs_prop / num_prop
  prec_conserv = TPs_gt   / num_prop

  recall = TPs_gt / num_gt

  return prec_conserv, recall
end



end#module
