#!/usr/bin/env julia

#=
   Out of Core (OOC)
=#

module main_ooc


unshift!(LOAD_PATH,".") #temporary


import io_u    # I/O Utils
import pinky_u # Pinky-Specific Utils
import seg_u   # Segmentation Utils
import chunk_u # Chunking Utils
import mfot    # Median-Over-Threshold Filter
import utils   # General Utils


#lines using these should be marked with
#param
include("parameters.jl")


#------------------------------------------
# Command-line arguments

# Current setup is designed for comparison
# tests with incore version
network_output_filename = ARGS[1];
segmentation_filename   = ARGS[2];
output_prefix           = ARGS[3];

#------------------------------------------


function main( segmentation_fname, output_prefix )

  seg, sem_output = init_datasets( segmentation_fname )

  vol_shape = size(seg)
  seg_bounds = [1,1,1] => collect(vol_shape) #vsincore test
  seg_offset = collect(seg_bounds.first) - 1;


  #param
  scan_chunk_bounds = chunk_u.chunk_bounds( vol_shape, scan_chunk_shape )


  processed_voxels = Set{Tuple{Int,Int,Int}}();
  sizehint!(processed_voxels, set_size_hint) #param

  edges = Array{Tuple{Int,Int},1}();
  locations = Array{Tuple{Int,Int,Int},1}();
  voxels = Vector{Vector{Tuple{Int,Int,Int}}}();

  psd_w = chunk_u.init_inspection_window( w_radius, sem_dtype ) #param
  seg_w = chunk_u.init_inspection_window( w_radius, seg_dtype ) #param

  for scan_bounds in scan_chunk_bounds

    println("Scan Chunk $(scan_bounds) ")

    ins_block, block_offset = chunk_u.fetch_inspection_block(
                                                      sem_output, scan_bounds,
                                                      seg_offset, w_radius,
                                                      seg_bounds ) #param
    seg_block, segb_offset  = chunk_u.fetch_inspection_block(
                                                      seg,        scan_bounds,
                                                      [0,0,0],    w_radius,
                                                      seg_bounds ) #param


    scan_chunk = chunk_u.fetch_chunk( sem_output, scan_bounds, seg_offset )


    scan_seg_offset = scan_bounds.first - 1;
    scan_global_offset = scan_seg_offset + seg_offset;

    semmap, _ = utils.make_semantic_assignment( seg_block, ins_block, [2,3] )

    psd_p         = scan_chunk[:,:,:,vol_map["PSD"]];
    psd_ins_block = ins_block[:,:,:,vol_map["PSD"]];

    println("Block median filter")
    #param
    @time psd_ins_block = mfot.median_over_threshold_filter( psd_ins_block, mfot_radius, cc_thresh )
    println("Chunk Median Filtering")
    #param
    @time psd_p = mfot.median_over_threshold_filter( psd_p, mfot_radius, cc_thresh )

    #extracted everything we need from here
    ins_block = nothing
    scan_chunk = nothing
    gc()

    #println("block offset: $(block_offset)")
    #println("scan_seg_offset: $(scan_seg_offset)")
    #println("scan_global_offset: $(scan_global_offset)")
    #println("ins block size: $(size(psd_ins_block))")

    process_scan_chunk!( psd_p, psd_ins_block, seg_block, semmap,
                         edges, locations, voxels, processed_voxels,

                         psd_w, seg_w,

                         scan_seg_offset, scan_global_offset,
                         block_offset, seg_bounds
                         )

    println("") #adding space to output

  end

  println("Saving edge information")
  io_u.save_edge_file( edges, locations, 1:length(locations),
                       "$(output_prefix)_edges.csv" )
  io_u.save_voxel_file( voxels, 1:length(locations),
                       "$(output_prefix)_voxels.csv")

end


function init_datasets( segmentation_filename )

  println("Reading segmentation file...")
  @time seg    = io_u.read_h5( segmentation_filename )

  # println("Initializing semantic H5Array...")
  # sem_output = pinky_u.init_semantic_arr()
  println("Reading output file...")
  @time sem_output = io_u.read_h5( network_output_filename )

  seg, sem_output
end



function process_scan_chunk!( psd_p, inspection_block, seg_block, semmap,
  edges, locations, voxels, processed_voxels,
  psd_w, seg_w,
  scan_seg_offset, scan_global_offset,
  inspection_global_offset, seg_bounds )

  #this will usually be the scan_chunk_shape, but
  # isn't likely to be so at the boundaries
  chunk_shape = size(psd_p)

  #translating the bounds of the segmentation volume
  # to those of the inspection window (and seg block?)
  ins_bounds = (seg_bounds.first  - inspection_global_offset) =>
               (seg_bounds.second - inspection_global_offset)


  for i in eachindex(psd_p)


    if !psd_p[i] continue end
    #if isnan(psd_p[i]) continue end


    isub        = ind2sub(chunk_shape,i)
    isub_global = utils.tuple_add( isub,        scan_global_offset )
    isub_ins    = utils.tuple_add( isub_global, -inspection_global_offset )


    if isub_global in processed_voxels
      pop!(processed_voxels, isub_global)
      continue
    end


    println("Processing potential synapse at index: $(isub_global)")
    offset_w = chunk_u.fill_inspection_window!( psd_w,
                              inspection_block, isub_ins,
                              w_radius, ins_bounds );
    chunk_u.fill_inspection_window!( seg_w,
                              seg_block, isub_ins,
                              w_radius, ins_bounds );

    #@assert size(psd_w) == size(seg_w)

    isub_w = utils.tuple_add( isub_ins, -offset_w )

    #debug
    #println("isub: $(isub)")
    #println("isub_seg: $(isub_seg)")
    #println("isub_global: $(isub_global)")
    #println("isub_ins: $(isub_ins)")
    #println("ins_bounds: $(ins_bounds)")
    #println("offset_w: $(offset_w)")
    #println("isub_w: $(isub_w)")
    #return

    process_synapse!( psd_w, seg_w, isub_w,
                      inspection_global_offset + offset_w,
                      semmap,
                      edges, locations, voxels, processed_voxels )
  end
end



function process_synapse!( psd_p, seg, i, offset, semmap,
  edges, locations, voxels, processed_voxels )

  syn, new_voxels = seg_u.connected_component3D( psd_p, i, cc_thresh )


  new_voxels = utils.convert_to_global_coords( new_voxels, offset )

  union!(processed_voxels, new_voxels)
  pop!(processed_voxels, utils.tuple_add(i,offset) )


  if length(new_voxels) <= size_thresh return end #param


  seg_u.dilate_by_k!( syn, dilation_param ) #param
  synapse_members, _ = utils.find_synaptic_edges( syn, seg, semmap,
                                                vol_map["axon"],
                                                vol_map["dendrite"])
  #if synapse deemed invalid (by semantic info)
  if synapse_members[1] == (0,0) return end


  #change to local coordinates?
  location = utils.coord_center_of_mass( new_voxels )

  println("Accepted synapse - adding information...")
  println(synapse_members)
  push!(locations, location)
  push!(edges, synapse_members[1])
  push!(voxels, new_voxels)

end


main( segmentation_filename, output_prefix )
#------------------------------------------

end#module end
