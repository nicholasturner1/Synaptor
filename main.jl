#!/usr/bin/env julia

#=
    In Core Processing Main
=#
#WARNING - this performs slightly different processing than
# main_ooc (no median filtering business atm)


#temporary
unshift!(LOAD_PATH,".")


import io_u  # I/O Utils
import seg_u # Segmentation Utils
import utils # General Utils

#------------------------------------------
# Command-line arguments

net_output_filename = ARGS[1];
segmentation_filename = ARGS[2];
output_prefix = ARGS[3];
#------------------------------------------

#lines using these should be marked with
#param
include("parameters.jl")


println("Reading network output file...")
output = io_u.read_h5( net_output_filename )
println("Reading segmentation file...")
seg    = io_u.read_h5( segmentation_filename )


println("Assigning segments to semantic categories...") #param
@time sem_map, _ = utils.make_semantic_assignment( seg, output,
                                               [vol_map["axon"],
                                               vol_map["dendrite"]] )


println("Forming synapse segments at $(cc_thresh)...") #param
@time syn_segs = seg_u.connected_components3D(
                    output[:,:,:,vol_map["PSD"]], cc_thresh )


println("Filtering by size threshold $(size_thresh)...") #param
@time seg_u.filter_segments_by_size!( syn_segs, size_thresh )


println("Finding segment locations")
@time locations = seg_u.centers_of_mass( syn_segs );


println("Dilating remaining segments by $(dilation_param)...")
dilated_segs = deepcopy(syn_segs)
@time seg_u.dilate_by_k!( dilated_segs, dilation_param ) #param


println("Deriving synaptic edge list") #param
@time edges, valid_segments = utils.find_synaptic_edges( dilated_segs, seg, sem_map,
                                                     vol_map["axon"],vol_map["dendrite"] )


locations = [ locations[ segid ] for segid in valid_segments ];
seg_u.filter_segments_by_ids!( syn_segs, valid_segments );


println("Saving edge information")
io_u.save_edge_file( edges, locations, 1:length(edges), "$(output_prefix)_edges.csv" )
println("Saving semantic mapping")
io_u.write_map_file( "$(output_prefix)_semmap.csv", sem_map );
println("Saving synaptic segments")
io_u.write_h5( syn_segs, "$(output_prefix)_seg.h5" )
