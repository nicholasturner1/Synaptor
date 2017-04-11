module EdgeFinders
#See edgefinder.jl for a description for why edge finders are useful

#EF - EdgeFinder Interface
export assign_aux_params!, assign_aux_vols!, assign_ccs!
export findedges, filteredges
#SemanticEF
export SemanticEdgeFinder, findedges_w_sem
#PrePostEF
export PrePostEdgeFinder, findedges_w_prepost
#VesicleEF
export VesicleEdgefinder, findedges_w_ves

#General Utils and Interfaces
include("utils.jl")
include("edgefinder.jl"); using .EF


#Specific EdgeFinders
#include("VesicleEdgeFinder.jl"); using .VesicleEF
include("SemanticEdgeFinder.jl"); using .SemanticEF
include("PrePostEdgeFinder.jl"); using .PrePostEF

end
