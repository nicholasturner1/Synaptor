module EdgeFinders
#See basic.jl for a description of why edge finders are useful

#Basic - Interface & Defaults
export findedges, filteredges
export assign_aux_params!, assign_aux_vols!
export make_ccs!, get_ccs, compute_cc_stats
export filter_by_size!, filter_by_id!, dilate_ccs!
export findcontinuations
#SemanticEF
export SemanticEdgeFinder, findedges_w_sem
#PrePostEF
export PrePostEdgeFinder, findedges_w_prepost
#VesicleEF
export VesicleEdgefinder, findedges_w_ves

#General Utils and Interfaces
include("utils.jl")
include("basic.jl"); using .Basic


#Specific EdgeFinders
#include("vesicleef.jl"); using .VesicleEF
include("semanticef.jl"); using .SemanticEF
include("prepostef.jl"); using .PrePostEF

end
