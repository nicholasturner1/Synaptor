module Consolidation

export find_new_continuations
export consolidate_continuations
export consolidate_ids, consolidate_edge_dict, apply_id_maps

include("continuations.jl"); using .Continuations
include("conscontinuations.jl"); using .ConsolidateContinuations
include("consids.jl"); using .ConsolidateIDs

end
