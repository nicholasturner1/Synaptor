#!/usr/bin/env julia

module continuation_u

type Continuation
  segid :: UInt32
  num_voxels :: Int
  center_of_mass :: Vector{Int}
  face_axis :: UInt8
  low_face :: Bool
  cont_voxels :: Vector{Vector{Int}}
  overlaps :: Dict{UInt32,Int} #not finalized
  overlap_semantics :: Dict{UInt32,UInt8} #not finalized
end


function seg_ids(c_list::Vector{Continuation})
  0#stub
end


function update_continuations!{T}(segment_volume::Array{T,3}, c_list::Vector{Continuation})
  0#stub
end


type ContinuationMap{T}
  mapping :: Dict{T,T}
end

ContinuationMap() = ContinuationMap(Dict());
ContinuationMap(T::DataType) = ContinuationMap(Dict{T,T}());


function Base.setindex!{T}(cm::ContinuationMap{T},dest,src)
  setindex!(cm.mapping,dest,src)
end


function Base.getindex{T}(cm::ContinuationMap{T},src)
  getindex(cm.mapping,src)
end

end #module
