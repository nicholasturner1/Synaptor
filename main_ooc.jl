#!/usr/bin/env julia

#=
   Out of Core (OOC) Processing

=#

module main_ooc


unshift!(LOAD_PATH,".") #temporary


import io_u        # I/O Utils
import seg_u       # Segmentation Utils
import chunk_u     # Chunking Utils
import vol_u       # Data Volume Utils
import utils       # General Utils
import contin_u    # Handling Segment Continuations
import mask_u      # Masking Utilities

#------------------------------------------
# Command-line arguments

config_filename = ARGS[1]
#------------------------------------------

#lines using these should be marked with
#param
include("parameters.jl")
include(config_filename)



function main( network_output_filename, segmentation_fname, output_prefix )

  #Reading/Initializing Data
  seg = io_u.import_dataset( segmentation_fname, seg_incore )#config
  sem_output = io_u.import_dataset( network_output_filename, sem_incore )#config

  #params
  slice_masks = nothing;
  if mask_poly_fname != nothing slice_masks = io_u.read_single_map(mask_poly_fname) end

  #Figuring out where I can index things without breaking anything
  seg_origin_offset  = seg_start - 1;#param
  seg_bounds  = chunk_u.bounds( seg )#param
  sem_bounds  = chunk_u.bounds( sem_output, seg_origin_offset )#param
  scan_bounds = scan_start_coord => scan_end_coord;#param
  scan_rel_offset = scan_start_coord - 1; #param

  #TODO write this instead#check_bounds( seg_bounds, sem_bounds, seg_origin_offset, DEBUG )#param
  valid_sem_bounds = chunk_u.intersect_bounds( sem_bounds, seg_bounds, seg_origin_offset )#param
  valid_seg_bounds = chunk_u.intersect_bounds( seg_bounds, sem_bounds, -seg_origin_offset )#param

  if DEBUG
    println("seg_bounds: $seg_bounds")
    println("sem_bounds: $sem_bounds")
    println("seg_origin_offset: $seg_origin_offset")
    println("scan_bounds: $scan_bounds")
    println("valid_seg_bounds: $valid_seg_bounds")
  end

  @assert vol_u.in_bounds( scan_bounds, valid_seg_bounds )

  scan_vol_shape = chunk_u.vol_shape( scan_bounds ) #param

  #Init
  #param
  chunk_bounds = chunk_u.BoundArray( scan_vol_shape, scan_chunk_shape, scan_rel_offset )
  continuation_arr = contin_u.ContinuationArray( seg_dtype, size(chunk_bounds) )
  conts_to_merge = Vector{Tuple{Int,Int}}()


  edges = Dict{Int,Tuple{Int,Int}}();
  locations = Dict{Int,Vector{Int}}();
  sizes = Dict{Int,Int}();
  seg_out = io_u.create_seg_dset( "$(output_prefix)_seg.h5", 
                                  scan_vol_shape,
                                  seg_chunk_size,"main" )

  num_chunks = length(chunk_bounds)
  chunk_count = 1
  next_seg_id = 1
  sx,sy,sz = size(chunk_bounds)

  #Chunk Loop
  for z in 1:sz, y in 1:sy, x in 1:sx
    curr_bounds = chunk_bounds[x,y,z]

    println("Scan Chunk #$(chunk_count) of $(num_chunks): $(curr_bounds) ")

    println("Fetching Chunks...")
    @time output_chunk = chunk_u.fetch_chunk( sem_output, curr_bounds, seg_origin_offset )
    @time seg_chunk    = chunk_u.fetch_chunk( seg, curr_bounds )


    println("Making semantic assignment...")
    @time semmap, _ = utils.make_semantic_assignment( seg_chunk, output_chunk, [2,3] )


    psd_chunk = output_chunk[:,:,:,vol_map["PSD"]];
    #remove_artifact_output!(psd_chunk, bboxes) #TODO...maybe


    scan_offset = scan_rel_offset + seg_origin_offset;


    # we've extracted everything we need from these
    output_chunk = nothing; gc()


    if slice_masks != nothing

      ch_x,ch_y,ch_z = curr_bounds.first
      ch_size_z = size(psd_chunk,3)
      
      ch_polygon_list = mask_u.polygon_list( slice_masks, ch_z, ch_size_z )
      mask_u.mask_vol_by_polygons!( psd_chunk, ch_polygon_list, [ch_x,ch_y]-1 )
      
    end

    if DEBUG #param
     println("block offset: $(block_offset)")
     println("scan_offset: $(scan_offset)")
     println("scan_origin_offset: $(scan_origin_offset)")
     println("ins block size: $(size(psd_ins_block))")
     println("scan chunk size: $(size(psd_p))")
    end

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
    chunk_count += 1

  end

  println("Consolidating continuations")
  @time (new_es, new_ls, new_szs, mapping
  ) = contin_u.consolidate_continuations( continuation_arr, size_thresh, conts_to_merge )


  merge!(edges, new_es)
  merge!(locations, new_ls)
  merge!(sizes, new_szs)


  println("Saving edge information")
  io_u.write_map_file( "$(output_prefix)_edges.csv", edges, locations, sizes )
  io_u.write_map_file( "$(output_prefix)_mapping.csv", mapping )
end


"""

    process_scan_chunk!( psd_p, seg, semmap, edges, locations, sizes,
                         chunk_offset, cont_arr, chunk_index, next_seg_id )
"""
function process_scan_chunk!( psd_p, seg, semmap,
                              edges, locations, sizes, chunk_offset,
                              cont_arr, chunk_index, next_seg_id )

  #See if any segments might not be complete from other chunks
  c_list = contin_u.find_continuations_to_apply( cont_arr, chunk_index )


  #Filling in continuations and new segments
  (segments, next_seg_id, to_merge
  ) = seg_u.fill_in_connected_components( psd_p, next_seg_id, c_list, cc_thresh )


  #Determining continuations within this chunk
  new_c_list = contin_u.find_new_continuations( segments, size(cont_arr),
                                                      chunk_index )
  cont_arr[chunk_index...] = new_c_list
  cont_ids = contin_u.segids(new_c_list)


  #Finding segment sizes
  new_sizes = seg_u.segment_sizes(segments)
  contin_u.update_sizes!(cont_arr[chunk_index...], new_sizes)


  #Finding non-continuation segments under size threshold
  # (continuations may have more voxels somewhere else)
  under_thresh = filter( (k,v) -> v < size_thresh, new_sizes )#param
  filter!( (k,v) -> !(k in cont_ids), under_thresh )
  seg_u.filter_out_segments_by_ids!( segments, collect(keys(under_thresh)) )
  #TODO make a fn for this


  new_locs = seg_u.centers_of_mass( segments )
  #adjusting locations to offset
  new_locs = Dict( k => v + chunk_offset for (k,v) in new_locs )
  contin_u.update_locs!(cont_arr[chunk_index...], new_locs)


  to_dilate = copy(segments)
  seg_u.dilate_by_k!( to_dilate, dilation_param )#param


  (new_edges, invalid_edges, overlap
  ) = utils.find_synaptic_edges(to_dilate, seg, semmap, 
                                vol_map["axon"], vol_map["dendrite"])
  
  #Filtering out semantic mismatches w/o continuations
  filter!( x -> !(x in cont_ids), invalid_edges)
  seg_u.filter_out_segments_by_ids!( segments, invalid_edges )

  #filtering out continuations from edges, locs, and sizes. 
  # We can rm continuations at this point bc their info has been
  # stored already, and they might corrupt the edge lists since
  # we haven't made final decisions about them yet
  filter!( (k,v) -> !(k in cont_ids), new_edges )
  #filter!( (k,v) -> (new_sizes[k] >= size_thresh), new_edges )
  filter!( (k,v) -> (k in keys(new_edges)), new_locs )
  filter!( (k,v) -> (k in keys(new_edges)), new_sizes )


  #Recording how often each continuation overlaps with
  # the morphological segments we've seen so far
  contin_u.update_overlaps!(cont_arr[chunk_index...], overlap, semmap)
  
  
  merge!(edges, new_edges)
  merge!(locations, new_locs)
  merge!(sizes, new_sizes)
  
  segments, next_seg_id, to_merge
end



main( network_output_filename, segmentation_filename, output_prefix )
#------------------------------------------

end#module end
