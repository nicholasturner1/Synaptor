module SegUtilsTests

using Base.Test

@testset "SegUtils" begin


include("dilation.jl")
include("overlap.jl")
include("conncomps.jl")
include("conscomps.jl")
include("semanticmap.jl")


end #@testset SegUtils

end #module SegUtilsTests
