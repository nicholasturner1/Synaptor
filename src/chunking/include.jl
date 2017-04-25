module Chunking

export BBox
export chunk_bounds, aligned_bounds

include("bbox.jl"); using .BBoxes
include("chunkbounds.jl"); using .ChunkBounds

end #module Chunking
