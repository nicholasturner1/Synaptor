#!/usr/bin/env julia

#=
   Out of Core (OOC) Processing

=#

module main_ooc


unshift!(LOAD_PATH,".") #temporary


import io_u           # I/O Utils
import pinky_u        # Pinky-Specific Utils
import seg_u          # Segmentation Utils
import chunk_u        # Chunking Utils
import mfot           # Median-Over-Threshold Filter
import vol_u          # Data Volume Utils
import utils          # General Utils
import omni_u         # MST Utils
import continuation_u # Handling Segment Continuations

using BigWrappers

#------------------------------------------
# Command-line arguments

config_filename = ARGS[1]
#------------------------------------------

#lines using these should be marked with
#param
include("parameters.jl")
include(config_filename)


function main_test( output_filename, segmentation_filename )

  println("Reading input...")
  @time output = io_u.read_h5(output_filename)
  @time seg = io_u.read_h5(segmentation_filename)
  @time seg_out = io_u.create_seg_dset( "test_seg.h5", size(seg), [1164,1164,136],"main" )

  cbs = chunk_u.BoundArray(size(seg), [1024,1024,256], [0,0,0])
  c_arr = continuation_u.ContinuationArray( seg_dtype, size(cbs) )#param

  
  #edges = Dict{Int,Tuple{sT,sT}}();
  edges = Dict{Int,Tuple{Int,Int}}();
  sizes = Dict{Int,Int}();
  locations = Dict{Int,Vector{Int}}();

  println("Making semantic assignment...")
  @time semmap, _ = utils.make_semantic_assignment( seg, output, [2,3] )

  psd_vol = output[:,:,:,vol_map["PSD"]];

  i = 1; num_chunks = length(cbs)
  next_seg_id = 1
  sx,sy,sz = size(cbs)
  conts_to_merge = Vector{Tuple{Int,Int}}()

  for z in 1:sz, y in 1:sy, x in 1:sx
    println("chunk $i of $num_chunks, $(cbs[x,y,z])")
    println("next id: $next_seg_id")
    seg_chunk = chunk_u.fetch_chunk(seg, cbs[x,y,z])
    psd_chunk = chunk_u.fetch_chunk(psd_vol, cbs[x,y,z])

    @time (psd_segments, next_seg_id, to_merge
    ) = process_scan_chunk!( psd_chunk, seg_chunk, semmap,
                             edges, locations, sizes, cbs[x,y,z].first-1,
                             c_arr, [x,y,z],
                             next_seg_id )

    zb = chunk_u.zip_bounds( cbs[x,y,z] )
    @time seg_out[zb...] = psd_segments

    i += 1
    append!(conts_to_merge, to_merge)
  end


  # we've extracted everything we need from these
  output_block = nothing; gc()

  @time (new_es, new_ls, new_szs, mapping
  ) = continuation_u.consolidate_continuations( c_arr, conts_to_merge )

  merge!(edges, new_es)
  merge!(locations, new_ls)
  merge!(sizes, new_szs)


  io_u.write_map_file("test_results.csv",edges, locations, sizes)
  io_u.write_map_file("test_mapping.csv",mapping)
  println("c_list, $([Int(c.segid) for c in c_arr[1,1,1]])")
end

function main( network_output_filename, segmentation_fname, output_prefix )

  seg, sem_output = init_datasets( segmentation_fname, network_output_filename )


  #Figuring out where I can index things without breaking anything
  seg_origin_offset  = seg_start - 1;#param
  #seg_bounds  = chunk_u.bounds( seg )#param
  #sem_bounds  = chunk_u.bounds( sem_output, seg_origin_offset )
  seg_bounds  = bounds( seg )#param
  sem_bounds  = bounds( sem_output, seg_origin_offset )#param

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
  continuation_arr = continuation_u.ContinuationArray( seg_dtype, size(chunk_bounds) )
  conts_to_merge = Vector{Tuple{Int,Int}}()


  edges = Dict{Int,Tuple{Int,Int}}();
  locations = Dict{Int,Vector{Int}}();
  sizes = Dict{Int,Int}();
  seg_out = io_u.create_seg_dset( "$(output_prefix)_seg.h5", 
                                  scan_vol_shape,
                                  seg_chunk_size,"main" )

  num_chunks = length(chunk_bounds)
  curr_chunk = 1
  next_seg_id = 1
  sx,sy,sz = size(chunk_bounds)
  for z in 1:sz, y in 1:sy, x in 1:sx
    curr_bounds = chunk_bounds[x,y,z]

    println("Scan Chunk #$(curr_chunk) of $(num_chunks): $(curr_bounds) ")

    println("Fetching Chunks...")
    @time output_chunk = chunk_u.fetch_chunk( sem_output, curr_bounds, seg_origin_offset )
    @time seg_chunk    = chunk_u.fetch_chunk( seg, curr_bounds )


    println("Making semantic assignment...")
    @time semmap, _ = utils.make_semantic_assignment( seg_chunk, output_chunk, [2,3] )


    psd_chunk = output_chunk[:,:,:,vol_map["PSD"]];
    #remove_artifact_output!(psd_chunk, bboxes) #TODO


    scan_offset = scan_bounds.first - 1 + seg_origin_offset;

    # println("block offset: $(block_offset)")
    # println("scan_offset: $(scan_offset)")
    # println("scan_origin_offset: $(scan_origin_offset)")
    # println("ins block size: $(size(psd_ins_block))")
    # println("scan chunk size: $(size(psd_p))")


    # we've extracted everything we need from these
    output_chunk = nothing; gc()


    println("Processing chunk")
    @time (psd_segments, next_seg_id, to_merge
    ) = process_scan_chunk!( psd_chunk, seg_chunk, semmap,
                             edges, locations, sizes, curr_bounds.first - 1,
                             continuation_arr, [x,y,z],
                             next_seg_id )


    append!(conts_to_merge, to_merge)

    #Writing chunk to segmentation
    println("Writing chunk")
    zb = chunk_u.zip_bounds( curr_bounds.first  - scan_rel_offset =>
                             curr_bounds.second - scan_rel_offset )
    @time seg_out[zb...] = psd_segments

    println("") #adding space to output
    curr_chunk += 1

  end

  println("Consolidating continuations")
  @time (new_es, new_ls, new_szs, mapping
  ) = continuation_u.consolidate_continuations( continuation_arr, conts_to_merge )

  merge!(edges, new_es)
  merge!(locations, new_ls)
  merge!(sizes, new_szs)


  println("Saving edge information")
  io_u.write_map_file( "$(output_prefix)_edges.csv", edges, locations, sizes )
  io_u.write_map_file( "$(output_prefix)_mapping.csv", mapping )
end


function init_datasets( segmentation_filename, network_output_filename )

  println("Reading segmentation file...")
  #BigArray
  @time seg = BigWrapper(segmentation_filename)
  #@time seg    = io_u.read_h5( segmentation_filename,
  #                             seg_incore, seg_dset_name )#param

  if network_output_filename != nothing
    println("Reading semantic file...")
    #@time sem_output = io_u.read_h5( network_output_filename, sem_incore )#param
    #@time sem_output = H5sBigArray(network_output_filename);
    @time sem_output = BigWrapper(network_output_filename);
  else
    println("Initializing semantic H5Array...")
    sem_output = pinky_u.init_semantic_arr()
  end

  seg, sem_output
end


function process_scan_chunk!( psd_p, seg, semmap,
                              edges, locations, sizes, chunk_offset,
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
  cont_ids = continuation_u.segids(new_c_list)


  #Finding segment sizes
  new_sizes = seg_u.segment_sizes(segments)
  continuation_u.update_sizes!(cont_arr[chunk_index...], new_sizes)


  #Finding non-continuation segments under size threshold
  # (continuations may have more voxels somewhere else)
  under_thresh = filter( (k,v) -> v < size_thresh, new_sizes )#param
  filter!( (k,v) -> !(k in cont_ids), under_thresh )
  seg_u.filter_out_segments_by_ids!( segments, collect(keys(under_thresh)) )
  #TODO make a fn for this


  new_locs = seg_u.centers_of_mass( segments )
  #adjusting locations to offset
  new_locs = Dict( k => v + chunk_offset for (k,v) in new_locs )
  continuation_u.update_locs!(cont_arr[chunk_index...], new_locs)


  to_dilate = copy(segments)
  seg_u.dilate_by_k!( to_dilate, dilation_param )#param


  (new_edges, invalid_edges, overlap
  ) = utils.find_synaptic_edges(to_dilate, seg, semmap, 
                                vol_map["axon"], vol_map["dendrite"])
  
  #Filtering out semantic mismatches w/o continuations
  filter!( x -> !(x in cont_ids), invalid_edges)
  seg_u.filter_out_segments_by_ids!( segments, invalid_edges )
  filter!( (k,v) -> !(k in invalid_edges), new_locs )
  filter!( (k,v) -> !(k in keys(edges)), new_sizes )

  continuation_u.update_overlaps!(cont_arr[chunk_index...], overlap, semmap)
  
  
  merge!(edges, new_edges)
  merge!(locations, new_locs)
  merge!(sizes, new_sizes)
  
  segments, next_seg_id, to_merge
end



main( network_output_filename, segmentation_filename, output_prefix )
#main_test( network_output_filename, segmentation_filename )
#------------------------------------------

end#module end
