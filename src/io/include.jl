module InputOutput

#BasicIO
export read_edge_file
export read_semmap, write_semmap
#ConsolidationIO
export write_continuation, write_continuations
#SegIO
export write_in_chunks, create_seg_dset

include("basic.jl"); using .BasicIO
include("continuations.jl"); using .ContinuationIO
include("segio.jl"); using .SegIO

end
