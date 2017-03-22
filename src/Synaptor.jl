module Synaptor

export PrePostEdgeFinder, findedges_w_prepost
export VesicleEdgefinder, findedges_w_ves
export SemanticEdgeFinder, findedges_w_sem


include("Types.jl")

include("segutils/include.jl"); using .SegUtils
include("edgefinders/include.jl"); using .EdgeFinders
#include("eval/include.jl")
include("proc/include.jl"); using .Processing

end # module
