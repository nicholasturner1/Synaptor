module Proc

#InCore
export process_single_chunk
export grid_search, f1_grid_search, f0p5_grid_search

include("utils.jl")
include("incore.jl"); using .InCore
include("outofcore.jl")#; using .OutOfCore

end
