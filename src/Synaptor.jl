module Synaptor


#IO
export read_edge_file
#Chunking
export BBox, chunk_bounds
#SegUtils
export relabel_data!, relabel_data, centers_of_mass
export filter_by_size, segment_sizes
export count_overlapping_labels, sum_overlap_weight
export find_max_overlaps
export connected_components3D, connected_components3D!
export consolidated_components
export make_semantic_assignment, make_assignment
export neighborhood_semmaps
#EdgeFinders
export PrePostEdgeFinder, findedges_w_prepost
export VesicleEdgefinder, findedges_w_ves
export SemanticEdgeFinder, findedges_w_sem
export assign_aux_params!, assign_aux_vols!
export make_ccs!, get_ccs, compute_cc_stats
export filter_by_size!, filter_by_id!, dilate_ccs!
export find_continuations
#Continuations
export find_continuations
#Eval
export prec_score, rec_score, f1score, f0p5score
#Proc
export process_chunk
export grid_search, f1_grid_search, f0p5_grid_search


include("Types.jl")


#I'm often dumping some names into the namespace since the explicitly exported
# fns within these modules shouldn't clash with anything else,
# and affording "toolbox"-type capabilities is very nice here.
#
#I've limited the global namespace here to fns which someone might reasonably
# use in one-off REPL sessions
include("io/include.jl"); using .IO
include("chunking/include.jl"); using .Chunking
include("segutils/include.jl"); using .SegUtils
include("continuations/include.jl"); using .Continuations
include("edgefinders/include.jl"); using .EdgeFinders
include("eval/include.jl"); using .Eval
include("proc/include.jl"); using .Proc


##OPTIONAL CLOUD UTILITIES
##export sendmsg, pullmsg, delmsg
##include("cloudutils/include.jl");


end # module Synaptor
