module InputOutput

#BasicIO
export read_edge_file, write_edge_file
export read_semmap, write_semmap
export write_idmap, read_idmap
#ConsolidationIO
export write_continuation, write_continuations
#SegIO
export write_in_chunks, create_seg_dset

include("basic.jl"); using .BasicIO
include("continuations.jl"); using .ContinuationIO
include("segio.jl"); using .SegIO

end
