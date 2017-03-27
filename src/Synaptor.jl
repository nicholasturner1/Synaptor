module Synaptor


#IO
export read_edge_file
#SegUtils
export relabel_data!, relabel_data, centers_of_mass
export filter_by_size, segment_sizes
export count_overlapping_labels, sum_overlap_weight
export find_max_overlaps
export connected_components3D, connected_components3D!
export consolidated_components
#EdgeFinders
export PrePostEdgeFinder, findedges_w_prepost
export VesicleEdgefinder, findedges_w_ves
export SemanticEdgeFinder, findedges_w_sem
export assign_aux_params!, assign_aux_vols!, assign_ccs!
export findedges
#Eval
export prec_score, rec_score, f1score, f0p5score
#Proc
export process_single_chunk
export grid_search, f1_grid_search, f0p5_grid_search


include("Types.jl")


#I'm often dumping some names into the namespace since the explicitly exported
# fns within these modules shouldn't clash with anything else,
# and affording "toolbox"-type capabilities is very nice here.
#
#I've limited the global namespace here to fns which someone might reasonably
# use in one-off REPL sessions
include("io/include.jl"); using .IO
include("segutils/include.jl"); using .SegUtils
include("edgefinders/include.jl"); using .EdgeFinders
include("eval/include.jl"); using .Eval
include("proc/include.jl"); using .Proc


end # module Synaptor
