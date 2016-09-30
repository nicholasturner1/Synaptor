#!/usr/bin/env julia

#temporary
unshift!(LOAD_PATH,".")

#import utils #testing
import utils 
import seg_u
import io_u

include("parameters.jl")

net_output_filename = ARGS[1];
segmentation_filename = ARGS[2];
output_prefix = ARGS[3];


println("Reading network output file...")
output = io_u.read_h5( net_output_filename )
println("Reading segmentation file...")
seg    = io_u.read_h5( segmentation_filename )


println("Assigning segments to semantic categories...")
@time sem_map, _ = utils.make_semantic_assignment( seg, output,
                                               [vol_map["axon"],
                                               vol_map["dendrite"]] )


println("Forming synapse segments at $(cc_thresh)...")
@time syn_segs = seg_u.connected_components3D(
                    output[:,:,:,vol_map["PSD"]], cc_thresh )


println("Filtering by size threshold $(size_thresh)...")
@time seg_u.filter_segments_by_size!( syn_segs, size_thresh )


println("Finding segment locations")
@time locations = seg_u.centers_of_mass( syn_segs );


println("Dilating remaining segments by $(dilation_param)...")
@time seg_u.dilate_by_k!( syn_segs, dilation_param )


println("Deriving synaptic edge list")
@time edges, valid_segments = utils.find_synaptic_edges( syn_segs, seg, sem_map,
                                                     vol_map["axon"],vol_map["dendrite"] )


locations = [ locations[ segid ] for segid in valid_segments ];

println("Saving edge information")
io_u.save_edge_file( edges, locations, 1:length(edges), "$(output_prefix)_edges.csv" )
println("Saving semantic mapping")
io_u.write_map_file( "$(output_prefix)_semmap.csv", sem_map );
