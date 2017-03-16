module SemanticEF


using ...Types
using ..EF


export SemanticEdgeFinder, findedges_w_sem


# Type parameters
reqd_args = [
("PSDsegs",    Array,   EF.VOL),
("MORPHsegs",  Array,   EF.VOL),
("semmap",     Dict,    EF.AUX_PARAM),
("axon_label", Integer, EF.AUX_PARAM),
("dend_label", Integer, EF.AUX_PARAM)
]


"""

    findedges_w_sem( psd_segs, seg, semmap, axon_label, dend_label)

Looks for edges within psd_segs by means of semantically classified
morphological segments. Declares edges between the axon and dendrite
which maximally overlap each psd segment, and labels psd segments that
can't fulfill this definition as invalid (e.g. a segment which only
overlaps a single segment)

### Inputs:
* `psd_segs`: postsynaptic density segments (usually connected components)
* `seg`: morphological segmentation of the same chunk
* `semmap`: semantic mapping of the morphological segments to categories. Only
         segments mapped to the axon_label or dend label will be considered
* `axon_label`, `dend_label`: sending and receiving labels (respectively)


### Outputs:
* `edges`: Dict mapping from psd_seg id to the morphological segments connected
         by that segment
* `invalid`: list of psd segment ids which were deemed invalid
* `overlap`: overlap matrix between psd segments and morphological segments

"""
function findedges_w_sem( psd_segs, seg, semmap, axon_label, dend_label )

  #if no semantic mapping, return default value for everything
  if length(keys(semmap)) == 0 return Dict(), [], spzeros(0,0) end


  overlap = segm.count_overlapping_labels( psd_segs, seg )


  seg_ids = extract_unique_rows(overlap)
  axons, dends = split_map_into_groups( semmap, [axon_label, dendrite_label] )

  axon_overlaps = overlap[:,axons]; dend_overlaps = overlap[:,dendrites];


  #if nothing overlaps, all segments are invalid
  if length(nonzeros(axon_overlaps)) == 0 || length(nonzeros(dend_overlaps)) == 0
    return Dict(), seg_ids, overlap
  end


  axon_max, axon_ids = find_max_overlaps( axon_overlaps, axons, seg_ids )
  dend_max, dend_ids = find_max_overlaps( dend_overlaps, dends, seg_ids )

  #only count edges if they overlap with SOME axon or dendrite
  valid_edges, invalid_edges = filter_edges( axon_max, dend_max )

  edges = Dict( sid => (axon_ids[sid],dend_ids[sid]) for sid in valid_edges )

  edges, invalid_edges, overlap
end


#===========================================
CLASS DEFINITION
===========================================#

#Explicitly wrapping the required args
explicit_args = map( x -> EF.EFArg(x[1],x[2],x[3]), reqd_args )

"""

    SemanticEdgeFinder <: EdgeFinder

Wrapper class for findedges_w_sem (see that fn's docs for details)
"""
type SemanticEdgeFinder <: Types.EdgeFinder
  reqs :: Vector{EF.EFArg}
  args :: Dict{String,Any}
  findedges :: Function

  SemanticEdgeFinder() = new(explicit_args, Dict{String,Any}(), findedges_w_sem)
end


function EF.find_edges(ef::SemanticEdgeFinder)

  EF.assert_specified(ef)

  psd_segs   = reqd_args["PSDsegs"]
  morph_segs = reqd_args["MORPHsegs"]
  semmap     = reqd_args["semmap"]
  axon_label = reqd_args["axon_label"]
  dend_label = reqd_args["dend_label"]

  ef.find_edges(psd_segs, morph_segs, semmap, axon_label, dend_label)
end


end #module SemanticEdgeFinder
