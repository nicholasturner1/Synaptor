module PrePostEF


using ...Types
using ..EF
using ..Utils


export PrePostEdgeFinder, findedges_w_prepost


#Type parameters
reqd_args = [
("PSDsegs",   Array, EF.VOL),
("MORPHsegs", Array, EF.VOL),
("PREvol",    Array, EF.SUBVOL),
("POSTvol",   Array, EF.SUBVOL)
]


"""

    findedges_w_prepost( psd_segs, seg, pre_vol, post_vol )

Looks for edges within psd_segs by means of network output identifying
pre and post synaptic terminals, along with morphological segments.
Declares edges when a pair of pre and post synaptic terminals overlap,
and declares the synaptic partners to be the morphological segments which
carry the most output weight with each terminal.

### Inputs:
* `psd_segs`: 4D vol, pre (vol1) and post (vol2) synaptic segments
* `seg`: morphological segmentation of the same chunk
* `pre_vol`: 3D presynaptic output volume
* `post_vol`: 3D postsynaptic output volume


### Outputs:
* `edges`: Dict mapping from a pair of pre and post synaptic ids to the
         morphological segments connected by those segments
"""
function findedges_w_prepost( psd_segs, seg, pre_vol, post_vol )


  @assert length(size(psd_segs)) == 4

  pre_segs = view(psd_segs,:,:,:,1)
  post_segs = view(psd_segs,:,:,:,2)

  pre_w  = Utils.sum_overlap_weight( pre_segs,  seg, pre_vol  )
  post_w = Utils.sum_overlap_weight( post_segs, seg, post_vol )
  overlap = Utils.count_overlapping_labels( pre_segs, post_segs )

  edges = Utils.find_pairs(overlap)
  segs  = assign_pairs(edges, pre_w, post_w)

  Dict( e => s for (e,s) in zip(edges,segs) )
end


"""

    assign_pairs( pairs, pre_weight_mat, post_weight_mat )

Assigns the edges to morphological segment pairs by max weight
"""
function assign_pairs( pairs, pre_weight_mat, post_weight_mat )

  pre_maxs,  pre_inds  = Utils.find_max_overlaps( pre_weight_mat )
  post_maxs, post_inds = Utils.find_max_overlaps( post_weight_mat )

  [ (pre_inds[s1],post_inds[s2]) for (s1,s2) in pairs ]
end


#===========================================
CLASS DEFINITION
===========================================#

#Explicitly wrapping the required args
explicit_args = map( x -> EF.EFArg(x[1],x[2],x[3]), reqd_args )


"""

    PrePostEdgeFinder <: EdgeFinder

Wrapper class for findedges_w_prepost (see that fn's docs for details)
"""
type PrePostEdgeFinder <: Types.EdgeFinder
  reqs :: Vector{EF.EFArg}
  args :: Dict{String,Any}
  findedges :: Function

  PrePostEdgeFinder() = new(explicit_args, Dict{String,Any}(), findedges_w_prepost)
end


function EF.find_edges(ef::PrePostEdgeFinder)

  EF.assert_specified(ef)

  psd_segs   = reqd_args["PSDsegs"]
  morph_segs = reqd_args["MORPHsegs"]
  pre_vol    = reqd_args["PREvol"]
  post_vol = reqd_args["POSTvol"]

  ef.find_edges(psd_segs, morph_segs, pre_vol, post_vol)
end


end #module PrePostEF
