
module EdgeFinders

include("utils.jl")
include("edgefinder.jl"); using .EF

include("VesicleEdgeFinder.jl")
include("SemanticEdgeFinder.jl")
include("PrePostEdgeFinder.jl")
include("FloodFillingEdgeFinder.jl")

end
