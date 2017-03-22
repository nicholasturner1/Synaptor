
module EdgeFinders
#See edgefinder.jl for a description for why edge finders are useful


#I'm often dumping the names into the namespace since the exported
# fns shouldn't clash with anything else, and affording "toolbox"-type
# capabilities is very nice here
export PrePostEdgeFinder, findedges_w_prepost
export VesicleEdgefinder, findedges_w_ves
export SemanticEdgeFinder, findedges_w_sem

#General Utils and Interfaces
include("utils.jl")
include("edgefinder.jl"); using .EF


#Specific EdgeFinders
#include("VesicleEdgeFinder.jl"); using .VesicleEF
include("SemanticEdgeFinder.jl"); using .SemanticEF
include("PrePostEdgeFinder.jl"); using .PrePostEF

end
