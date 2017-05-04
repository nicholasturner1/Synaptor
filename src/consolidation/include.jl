module Consolidation

#Continuations
export find_new_continuations
#ConsolidateContinuations
export consolidate_continuations, find_continuation_edges
#ConsolidateIDs
export consolidate_ids, consolidate_edge_dict, apply_id_maps
#ConsolidateDuplicates
export consolidate_dups
#ConsolidateFocalPoints
export consolidate_focal_points

include("continuations.jl"); using .Continuations
include("conscontinuations.jl"); using .ConsolidateContinuations
include("consids.jl"); using .ConsolidateIDs
include("consdups.jl"); using .ConsolidateDuplicates
include("consfps.jl"); using .ConsolidateFocalPoints

end
