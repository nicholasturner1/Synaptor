#!/usr/bin/env julia

#=
   Out of Core (OOC) Processing Testing module

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


function init_datasets( segmentation_filename, network_output_filename,
                        seg_incore=false, net_incore=false )

  seg = io_u.import_dataset( segmentation_filename, seg_incore )
  sem = io_u.import_dataset( network_output_filename, net_incore )
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
