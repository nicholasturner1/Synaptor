module EdgeFindersTests

using Base.Test

@testset "EdgeFinders" begin


include("utils.jl")
include("SemanticEdgeFinder.jl")
include("PrePostEdgeFinder.jl")


end #@testset EdgeFinders

end
