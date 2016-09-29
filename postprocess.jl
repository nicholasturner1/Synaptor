#!/usr/bin/env julia

#temporary
unshift!(LOAD_PATH,".")

#import utils #testing
import postprocess_u
import io_utils

include("parameters.jl")

net_output_filename = ARGS[1];
segmentation_filename = ARGS[2];
output_prefix = ARGS[3];


println("Reading network output file...")
output = io_utils.read_h5( net_output_filename )
println("Reading segmentation file...")
seg    = io_utils.read_h5( segmentation_filename )


println("Assigning segments to semantic categories...")
@time sem_map, _ = postprocess_u.make_semantic_assignment( seg, output,
                                               [vol_map["axon"],
                                               vol_map["dendrite"]] )


println("Forming synapse segments at $(cc_thresh)...")
@time syn_segs = postprocess_u.connected_components3D(
                    output[:,:,:,vol_map["PSD"]], cc_thresh )


println("Filtering by size threshold $(size_thresh)...")
@time postprocess_u.filter_segments_by_size!( syn_segs, size_thresh )


println("Finding segment locations")
@time locations = postprocess_u.centers_of_mass( syn_segs );


println("Dilating remaining segments by $(dilation_param)...")
@time postprocess_u.dilate_by_k!( syn_segs, dilation_param )


println("Deriving synaptic edge list")
@time edges, valid_segments = postprocess_u.find_synaptic_edges( syn_segs, seg,
                                                     sem_map, size_thresh,
                                                     vol_map["axon"],vol_map["dendrite"] )


locations = [ locations[ segid ] for segid in valid_segments ];

println("Saving edge information")
io_utils.save_edge_file( edges, locations, valid_segments, "$(output_prefix)_edges.csv" )
println("Saving semantic mapping")
io_utils.write_map_file( "$(output_prefix)_semmap.csv", sem_map );
