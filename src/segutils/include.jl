module SegUtils

#Utils
export relabel_data!, relabel_data, centers_of_mass
export filter_by_size, segment_sizes
#Overlap
export count_overlapping_labels, sum_overlap_weight
export find_max_overlaps
#ConnComps
export connected_components3D, connected_components3D!
#ConsComps
export consolidated_components, consolidated_components!
#Dilation
export dilate_by_k!
#SemanticMap
export make_semantic_assignment, make_assignment
export neighborhood_semmaps


include("utils.jl"); using .Utils
include("overlap.jl"); using .Overlap
include("conncomps.jl"); using .ConnComps
include("conscomps.jl"); using .ConsComps
include("dilation.jl"); using .Dilation
include("semanticmap.jl"); using .SemanticMap


end #module SegUtils
