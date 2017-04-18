module Proc

#InCore
export process_chunk, process_chunk_w_continuations
#GridSearch
export f1_grid_search, f0p5_grid_search
export prec_grid_search, rec_grid_search, prec_rec_grid_search

include("utils.jl")
include("incore.jl"); using .InCore
include("gridsearch.jl"); using .GridSearch
include("outofcore.jl")#; using .OutOfCore

end
