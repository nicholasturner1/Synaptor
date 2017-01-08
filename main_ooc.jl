#!/usr/bin/env julia

#=
   Out of Core (OOC) Processing

   Hope to clean this up a bit more soon...but we'll see
=#

module main_ooc


unshift!(LOAD_PATH,".") #temporary


import io_u    # I/O Utils
import pinky_u # Pinky-Specific Utils
import seg_u   # Segmentation Utils
import chunk_u # Chunking Utils
import mfot    # Median-Over-Threshold Filter
import vol_u   # Data Volume Utils
import utils   # General Utils
import omni_u  # MST Utils

using BigArrays.H5sBigArrays

#------------------------------------------
# Command-line arguments

config_filename = ARGS[1]
#------------------------------------------

#lines using these should be marked with
#param
include("parameters.jl")
include(config_filename)


function main( segmentation_fname, output_prefix )

  seg, sem_output = init_datasets( segmentation_fname, network_output_filename )


  #Figuring out where I can index things without breaking anything
  seg_origin_offset  = seg_start - 1;#param
  seg_bounds  = chunk_u.bounds( seg )#param
  sem_bounds  = chunk_u.bounds( sem_output, seg_origin_offset )

  valid_sem_bounds = chunk_u.intersect_bounds( sem_bounds, seg_bounds, seg_origin_offset )
  valid_seg_bounds = chunk_u.intersect_bounds( seg_bounds, sem_bounds, -seg_origin_offset )

  scan_bounds = scan_start_coord => scan_end_coord;
  #println("seg_bounds: $seg_bounds")
  #println("sem_bounds: $sem_bounds")
  #println("seg_origin_offset: $seg_origin_offset")
  #println("scan_bounds: $scan_bounds")
  #println("valid_seg_bounds: $valid_seg_bounds")
  @assert vol_u.in_bounds( scan_bounds, valid_seg_bounds )

  scan_vol_shape = chunk_u.vol_shape( scan_bounds ) #param

  scan_rel_offset = scan_start_coord - 1; #param
  #param
  chunk_bounds = chunk_u.BoundArray( scan_vol_shape, scan_chunk_shape, scan_rel_offset )
  continuation_arr = continuation_u.ContinuationArray( eltype(seg), size(chunk_bounds) )
  continuations_to_merge = Vector{Tuple{Int,Int}}()


  edges = Array{Tuple{Int,Int},1}();
  locations = Array{Tuple{Int,Int,Int},1}();

  num_scan_chunks = length(scan_chunk_bounds)
  curr_chunk = 1
  next_seg_id = 1
  sz,sy,sz = size(chunk_bounds)
  for z in 1:sz, y in 1:sy, x in 1:sz

    println("Scan Chunk #$(curr_chunk) of $(num_scan_chunks): $(curr_bounds) ")

    #want the inspection block to represent all valid mfot values
    # in the original volume which can be reached by an inspection window
    # within the scan chunk. Need to increase the window radius to acct
    # for the median filtering operation
    println("Fetching Chunks...")
    output_chunk = chunk_u.fetch_chunk( sem_output, chunk, seg_origin_offset )
    seg_chunk    = chunk_u.fetch_chunk( seg, chunk )


    println("Making semantic assignment...")
    @time semmap, _ = utils.make_semantic_assignment( seg_chunk, output_block, [2,3] )


    psd_chunk = output_block[:,:,:,vol_map["PSD"]];
    #remove_artifact_output!(psd_chunk, bboxes) #TODO


    scan_offset = scan_bounds.first - 1 + seg_origin_offset;

    # println("block offset: $(block_offset)")
    # println("scan_offset: $(scan_offset)")
    # println("scan_origin_offset: $(scan_origin_offset)")
    # println("ins block size: $(size(psd_ins_block))")
    # println("scan chunk size: $(size(psd_p))")


    # we've extracted everything we need from these
    output_block = nothing; gc()


    (psd_segments, next_seg_id, to_merge
    ) = process_scan_chunk!( psd_chunk, seg_chunk, semmap,
                             edges, locations, scan_offset,
                             continuation_arr, [x,y,z],
                             next_seg_id )


    #TODO Save chunk to h5
    append!(conts_to_merge, to_merge)

    println("") #adding space to output
    curr_chunk += 1

  end

  #TODO consolidate continuations
  (new_es, new_ls, mapping
  ) = continuation_u.consolidate_continuations( continuation_arr, conts_to_merge )

  merge!(edges, new_es)
  merge!(locations, new_ls)

  #TODO write continuation mapping

  println("Saving edge information")
  io_u.save_edge_file( edges, locations, 1:length(locations),
                       "$(output_prefix)_edges.csv" )
  io_u.save_voxel_file( voxels, 1:length(locations),
                       "$(output_prefix)_voxels.csv")

end


function init_datasets( segmentation_filename )

  println("Reading segmentation file...")
  @time seg    = io_u.read_h5( segmentation_filename,
                               seg_incore, seg_dset_name )#param

  if network_output_filename != nothing
    println("Reading semantic file...")
    #@time sem_output = io_u.read_h5( network_output_filename, sem_incore )#param
    @time sem_output = H5sBigArray(network_output_filename);
  else
    println("Initializing semantic H5Array...")
    sem_output = pinky_u.init_semantic_arr()
  end

  seg, sem_output
end


function process_scan_chunk!( psd_p, seg, semmap,
                              edges, locations, scan_offset
                              cont_arr, chunk_index, next_seg_id )

  #See if any segments might not be complete from other chunks
  c_list = continuation_u.find_continuations_to_apply( cont_arr, chunk_index )


  #Filling in continuations and new segments
  (segments, next_seg_id, to_merge
  ) = seg_u.fill_in_connected_components( psd_p, next_seg_id, c_list, cc_thresh )


  #Determining continuations within this chunk
  new_c_list = continuation_u.find_new_continuations( segments, size(cont_arr),
                                                      chunk_index )
  cont_arr[chunk_index...] = new_c_list
  cont_ids = continuation_u.seg_ids(new_c_list)


  #Finding segment sizes
  sizes = seg_u.segment_sizes(segments)
  continuation_u.update_sizes!(cont_arr[chunk_index...], sizes)


  #Finding non-continuation segments under size threshold
  # (continuations may have more voxels somewhere else)
  under_thresh = filter( (k,v) -> v < size_thresh, sizes )#param
  filter!( (k,v) -> !(k in cont_ids), under_thresh )
  seg_u.filter_out_segments_by_id!( segments, collect(keys(under_thresh)) )
  #TODO make a fn for this


  new_locs = seg_u.centers_of_mass( segments )
  continuation_u.update_locs!(cont_arr[chunk_index...], new_locs)


  to_dilate = copy(segments)
  seg_u.dilate_by_k!( segments, dilation_param )#param


  (new_edges, invalid_edges, overlap
  ) = utils.find_synaptic_edges(to_dilate, seg, semmap, 
                                vol_map["axon"], vol_map["dendrite"])
  
  #Filtering out semantic mismatches w/o continuations
  filter!( x -> !(x in cont_ids), invalid_edges)
  seg_u.filter_output_segments_by_id!( segments, invalid_edges )
  filter!( (k,v) -> !(k in invalid_edges), new_locs )

  continuation_u.update_overlaps!(cont_arr[chunk_index...], overlap, semmap)
  
  
  merge!(edges, new_edges)
  merge!(locations, new_locs)
  
  segments, next_id, to_merge
end



main( segmentation_filename, output_prefix )
#------------------------------------------

end#module end
