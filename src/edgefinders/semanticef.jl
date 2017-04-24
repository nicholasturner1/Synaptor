module SemanticEF


using ...Types
using ..Basic
using ..Utils
using ...SegUtils


export SemanticEdgeFinder, findedges_w_sem


# Type parameters
reqd_args = [
(:ccs,        AbstractArray,   Basic.VOL),
(:dil_ccs,    AbstractArray,   Basic.VOL),
(:MORPHsegs,  AbstractArray,   Basic.VOL),
(:PSDvol,     AbstractArray,   Basic.SUBVOL),
(:semmap,     Dict,            Basic.AUX_PARAM),
(:axon_label, Integer,         Basic.AUX_PARAM),
(:dend_label, Integer,         Basic.AUX_PARAM),
(:CCthresh,   Real,            Basic.AUX_PARAM),
(:SZthresh,   Real,            Basic.AUX_PARAM),
(:dilation,   Real,            Basic.AUX_PARAM)
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


  overlap = SegUtils.count_overlapping_labels( psd_segs, seg )
  overlap = expand_sparse_matrix_cols( overlap, maximum(keys(semmap)) )


  seg_ids = Utils.extract_unique_rows(overlap)
  axons, dends = Utils.split_map_into_groups( semmap, [axon_label, dend_label] )

  axon_overlaps = overlap[:,axons]; dend_overlaps = overlap[:,dends];


  #if nothing overlaps, all segments are invalid
  if length(nonzeros(axon_overlaps)) == 0 || length(nonzeros(dend_overlaps)) == 0
    return Dict(), seg_ids, overlap
  end


  axon_max, axon_ids = SegUtils.find_max_overlaps( axon_overlaps, axons )
  dend_max, dend_ids = SegUtils.find_max_overlaps( dend_overlaps, dends )

  #only count edges if they overlap with SOME axon or dendrite
  valid_edges, invalid_edges = _filter_edges( axon_max, dend_max )

  edges = Dict( sid => (axon_ids[sid],dend_ids[sid]) for sid in valid_edges )

  edges, invalid_edges, overlap
end


function expand_sparse_matrix_cols( sp::SparseMatrixCSC, n )

  sx,sy = size(sp)

  if sy == n  return sp  end

  num_new_cols = n - sy

  new_cols = spzeros(eltype(sp),sx,num_new_cols)

  hcat(sp, new_cols)
end


"""

    _filter_edges( max_ax_overlap, max_de_overlap )_

  Enacts filtering constraints on edges by means of semantic overlaps
"""
function _filter_edges( max_ax_overlap, max_de_overlap )

  num_psd_segs = length(max_ax_overlap)
  valid_edges, invalid_edges = Vector{Int}(), Vector{Int}();

  zT = valtype(max_ax_overlap)(0)
  for k in keys(max_ax_overlap)
    # println("k $k ax $(max_ax_overlap[k]) de $(max_de_overlap[k])")
    if max_ax_overlap[k] == zT || max_de_overlap[k] == zT
      push!(invalid_edges,k)
    else
      push!(valid_edges,k)
    end
  end

  valid_edges, invalid_edges
end


#===========================================
CLASS DEFINITION
===========================================#

#Explicitly wrapping the required args
explicit_args = map( x -> Basic.EFArg(x[1],x[2],x[3]), reqd_args )

"""

    SemanticEdgeFinder <: EdgeFinder

Wrapper class for findedges_w_sem (see that fn's docs for details)
"""
type SemanticEdgeFinder <: Types.EdgeFinder
  reqs :: Vector{Basic.EFArg}
  args :: Dict{Symbol,Any}
  findedges :: Function

  SemanticEdgeFinder() = new(explicit_args, Dict{Symbol,Any}(), findedges_w_sem)
end


function Basic.findedges(ef::SemanticEdgeFinder)

  Basic.assert_specified(ef)

  psd_segs   = ef.args[:dil_ccs]
  morph_segs = ef.args[:MORPHsegs]
  semmap     = ef.args[:semmap]
  axon_label = ef.args[:axon_label]
  dend_label = ef.args[:dend_label]

  ef.findedges(psd_segs, morph_segs, semmap, axon_label, dend_label)
end


end #module SemanticEdgeFinder
