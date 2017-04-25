module Consolidation

#Continuations
export find_new_continuations
#ConsolidateContinuations
export consolidate_continuations
#ConsolidateIDs
export consolidate_ids, consolidate_edge_dict, apply_id_maps
#ConsolidateDuplicates
export consolidate_dups

include("continuations.jl"); using .Continuations
include("conscontinuations.jl"); using .ConsolidateContinuations
include("consids.jl"); using .ConsolidateIDs
include("consdups.jl"); using .ConsolidateDuplicates

end
