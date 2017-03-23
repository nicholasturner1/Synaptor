module PrePostEF


using ...Types
using ...SegUtils
using ..EF
using ..Utils


export PrePostEdgeFinder, findedges_w_prepost


#Type parameters
reqd_args = [
(:SYNsegs,   AbstractArray, EF.VOL),
(:MORPHsegs, AbstractArray, EF.VOL),
(:PREvol,    AbstractArray, EF.SUBVOL),
(:POSTvol,   AbstractArray, EF.SUBVOL),
(:CCthresh,  Real,          EF.AUX_PARAM),
(:SZthresh,  Real,          EF.AUX_PARAM)
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
function findedges_w_prepost( syn_segs, seg, pre_vol, post_vol )


  @assert length(size(syn_segs)) == 4

  pre_segs = view(syn_segs,:,:,:,1)
  post_segs = view(syn_segs,:,:,:,2)

  pre_w  = SegUtils.sum_overlap_weight( pre_segs,  seg, pre_vol  )
  post_w = SegUtils.sum_overlap_weight( post_segs, seg, post_vol )
  overlap = SegUtils.count_overlapping_labels( pre_segs, post_segs )

  edges = Utils.find_pairs(overlap)
  segs  = assign_pairs(edges, pre_w, post_w)

  Dict( e => s for (e,s) in zip(edges,segs) )
end


"""

    assign_pairs( pairs, pre_weight_mat, post_weight_mat )

Assigns the edges to morphological segment pairs by max weight
"""
function assign_pairs( pairs, pre_weight_mat, post_weight_mat )

  pre_maxs,  pre_inds  = SegUtils.find_max_overlaps( pre_weight_mat )
  post_maxs, post_inds = SegUtils.find_max_overlaps( post_weight_mat )

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
  args :: Dict{Symbol,Any}
  findedges :: Function

  PrePostEdgeFinder() = new(explicit_args, Dict{Symbol,Any}(), findedges_w_prepost)
end


function EF.findedges(ef::PrePostEdgeFinder)

  EF.assert_specified(ef)

  psd_segs   = ef.args[:SYNsegs]
  morph_segs = ef.args[:MORPHsegs]
  pre_vol    = ef.args[:PREvol]
  post_vol = ef.args[:POSTvol]

  ef.findedges(psd_segs, morph_segs, pre_vol, post_vol)
end


function EF.assign_ccs!(ef::PrePostEdgeFinder, T=Int)

  pre_vol   = ef.args[:PREvol]
  post_vol  = ef.args[:POSTvol]
  cc_thresh = ef.args[:CCthresh]
  sz_thresh = ef.args[:SZthresh]

  synsegs = zeros(T,size(pre_vol)...,2)

  SegUtils.connected_components3D!( pre_vol,  view(synsegs,:,:,:,1), cc_thresh )
  SegUtils.connected_components3D!( post_vol, view(synsegs,:,:,:,2), cc_thresh )

  SegUtils.filter_by_size!( view(synsegs,:,:,:,1), sz_thresh )
  SegUtils.filter_by_size!( view(synsegs,:,:,:,2), sz_thresh )

  ef.args[:SYNsegs] = synsegs

end


end #module PrePostEF
