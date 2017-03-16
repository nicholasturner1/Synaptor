module PrePostEF


using ...Types
using ..EF


export PrePostEdgeFinder, findedges_w_prepost


#Type parameters
reqd_args = [
("PSDsegs",   Array, EF.VOL),
("MORPHsegs", Array, EF.VOL),
("PREvol",    Array, EF.SUBVOL),
("POSTvol",   Array, EF.SUBVOL)
]


"""
"""
function findedges_w_prepost( psd_segs, seg, pre_vol, post_vol )
  0#stub #NOTE INCOMPLETE
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
