#!/usr/bin/env julia
"""
   Postprocess Out of Core (OOC)
"""

module postprocess_ooc
#temporary
unshift!(LOAD_PATH,".")

#import utils #testing
import postprocess_u
import io_utils
import pinky_u
import vol_u

#lines using these should be marked with
#param
include("parameters.jl")

#------------------------------------------
#Comparison tests with incore version
network_output_filename = ARGS[1];
segmentation_filename   = ARGS[2];
semantic_map_filename   = ARGS[3];
output_prefix           = ARGS[4];

#------------------------------------------
#segmentation_filename = ARGS[1];
#semantic_map_filename = ARGS[2]
#output_prefix = ARGS[3];
#------------------------------------------


function main( segmentation_fname, semantic_map_fname, output_prefix )

  # seg, sem_output = init_datasets( segmentation_fname )
  #vsincore test
  seg, sem_output, semmap = init_datasets( segmentation_fname, semantic_map_fname )
  empty!(semmap) #temp muahahaha

  vol_shape = size(seg)
  # seg_bounds = pinky_u.bounds_from_file( segmentation_fname )
  seg_bounds = [1,1,1] => collect(vol_shape) #vsincore test
  seg_offset = collect(seg_bounds.first) - 1;


  #param
  scan_chunk_bounds = vol_u.chunk_bounds( vol_shape, scan_chunk_shape )


  processed_voxels = Set{Tuple{Int,Int,Int}}();
  sizehint!(processed_voxels, set_size_hint) #param

  edges = Array{Tuple{Int,Int},1}();
  locations = Array{Tuple{Int,Int,Int},1}();

  #Init memory uses
  psd_w = postprocess_u.initialize_inspection_window( w_radius, sem_dtype ) #param
  seg_w = postprocess_u.initialize_inspection_window( w_radius, seg_dtype ) #param
  # cc_vol  = zeros(UInt8, size(psd_w));
  # cc_mask = BitArray(size(psd_w));


  for scan_bounds in scan_chunk_bounds

    println("Scan Chunk $(scan_bounds) ")

    ins_block, block_offset = fetch_inspection_block( sem_output, scan_bounds,
                                                      seg_offset, w_radius,
                                                      seg_bounds ) #param
    seg_block, segb_offset  = fetch_inspection_block( seg,        scan_bounds,
                                                      [0,0,0],    w_radius,
                                                      seg_bounds )

    scan_chunk = fetch_sem_chunk( sem_output, scan_bounds, seg_offset )


    scan_seg_offset = scan_bounds.first - 1;
    scan_global_offset = scan_seg_offset + seg_offset;

    @time semmap, _ = postprocess_u.make_semantic_assignment( seg_block, ins_block, [2,3] )

    psd_p         = scan_chunk[:,:,:,vol_map["PSD"]];
    psd_ins_block = ins_block[:,:,:,vol_map["PSD"]];

    #extracted everything we need from here
    ins_block = nothing
    scan_chunk = nothing
    gc()

    #println("block offset: $(block_offset)")
    #println("scan_seg_offset: $(scan_seg_offset)")
    #println("scan_global_offset: $(scan_global_offset)")
    #println("ins block size: $(size(psd_ins_block))")

    @profile process_scan_chunk!( psd_p, psd_ins_block, seg_block, semmap,
                         edges, locations, processed_voxels,

                         psd_w, seg_w,

                         scan_seg_offset, scan_global_offset,
                         block_offset, seg_bounds
                         )
    println("") #adding space to output

  end

  println("Saving edge information")
  io_utils.save_edge_file( edges, locations, 1:length(locations),
                           "$(output_prefix)_edges.csv" )

end


function init_datasets( segmentation_filename, semantic_map_filename )

  println("Reading segmentation file...")
  @time seg    = io_utils.read_h5( segmentation_filename )

  # println("Initializing semantic H5Array...")
  # sem_output = pinky_u.init_semantic_arr()
  println("Reading output file...")
  @time sem_output = io_utils.read_h5( network_output_filename )

  println("Reading semantic file...")
  semmap = io_utils.read_map_file( semantic_map_filename, 1 )[1]

  seg, sem_output, semmap
  # seg, sem_output
end


function tuple_add( t::Tuple, a )
  (t[1]+a[1], t[2]+a[2], t[3]+a[3])
end


function fetch_sem_chunk( sem, bounds, offset )

  i_beg = bounds.first  + offset;
  i_end = bounds.second + offset;

  sem[i_beg[1]:i_end[1],
      i_beg[2]:i_end[2],
      # i_beg[3]:i_end[3]]
      i_beg[3]:i_end[3],:]
end


function fetch_seg_chunk( seg, bounds )

  i_beg, i_end = bounds;

  sem[i_beg[1]:i_end[1],
      i_beg[2]:i_end[2],
      i_beg[3]:i_end[3]]
end


function fetch_inspection_block( vol, scan_bounds, scan_offset,
  ins_window_radius, inspection_bounds )

  scan_shape = scan_bounds.second - scan_bounds.first + 1;
  scan_radius = round(Int, ceil(scan_shape / 2))

  block_radius = scan_radius + ins_window_radius

  scan_midpoint = scan_bounds.first + scan_radius - 1;

  scan_midpoint_global = scan_midpoint + scan_offset;

  postprocess_u.get_inspection_window(
                  vol, scan_midpoint_global,
                  block_radius, inspection_bounds )
end


function process_scan_chunk!( psd_p, inspection_block, seg_block, semmap,
  edges, locations, processed_voxels,
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


    if psd_p[i] < cc_thresh continue end
    if isnan(psd_p[i]) continue end


    isub        = ind2sub(chunk_shape,i)
    # isub_seg    = tuple_add( isub,        scan_seg_offset )
    isub_global = tuple_add( isub,        scan_global_offset )
    isub_ins    = tuple_add( isub_global, -inspection_global_offset )


    if isub_global in processed_voxels
      pop!(processed_voxels, isub_global)
      continue
    end


    println("Processing potential synapse at index: $(isub_global)")
    #@time psd_w, offset_w = postprocess_u.get_inspection_window(
    offset_w = postprocess_u.fill_inspection_window!( psd_w,
                              inspection_block, isub_ins,
                              w_radius, ins_bounds );
    #@time seg_w, _ = postprocess_u.get_inspection_window(
    postprocess_u.fill_inspection_window!( seg_w,
                              seg_block, isub_ins,
                              w_radius, ins_bounds );

    # @assert size(psd_p_w) == size(seg_w)

    isub_w = tuple_add( isub_ins, -offset_w )

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
                      edges, locations, processed_voxels )
  end

end


function process_synapse!( psd_p, seg, i, offset, semmap,
  edges, locations, processed_voxels )

  @time syn, new_voxels = postprocess_u.connected_component3D( psd_p, i, cc_thresh )
  #@time new_voxels = postprocess_u.connected_component3D!( psd_p, i, cc_vol, cc_mask, cc_thresh )

  new_voxels = postprocess_u.convert_to_global_coords( new_voxels, offset )

  union!(processed_voxels, new_voxels)
  pop!(processed_voxels, tuple_add(i,offset) )
  # println(processed_voxels)

  if length(new_voxels) <= size_thresh return end #param

  postprocess_u.dilate_by_k!( syn, dilation_param ) #param
  #postprocess_u.dilate_by_k!( cc_vol, dilation_param ) #param
  synapse_members, _ = postprocess_u.find_synaptic_edges( syn, seg, semmap, 0,
  #synapse_members, _ = postprocess_u.find_synaptic_edges( cc_vol, seg, semmap, 0,
                                                vol_map["axon"],
                                                vol_map["dendrite"])

  #if synapse deemed invalid (by semantic info)
  if synapse_members[1] == (0,0) return end

  #change to local coordinates?
  location = postprocess_u.coord_center_of_mass( new_voxels )

  println("Accepted synapse - adding information...")
  push!(locations, location)
  println(synapse_members)
  push!(edges, synapse_members[1])

end



main( segmentation_filename, semantic_map_filename, output_prefix )
#------------------------------------------

end#module end
