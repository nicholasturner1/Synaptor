module Chunking

export BBox
export chunk_bounds, aligned_bounds, seg_bboxes

include("bbox.jl"); using .BBoxes
include("cloudbbox.jl"); using .CloudBBoxes
include("chunkbounds.jl"); using .ChunkBounds
include("segbounds.jl"); using .SegBounds

end #module Chunking
