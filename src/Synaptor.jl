module Synaptor

export SemanticEdgeFinder, findedges_w_sem

include("Types.jl")

include("edgefinders/include.jl"); using .EdgeFinders
#include("eval/include.jl")
#include("proc/include.jl")

end # module
