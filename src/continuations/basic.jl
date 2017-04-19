module Basic

#Continuations represent segments which could pass onto the next
#chunk in a dataset which is too large to fit in RAM


export Continuation, AXIS, Face
export get_segid, get_voxels, get_overlaps, get_loc
export set_size!, set_loc!, push_overlap!


#Describing which face the continuation touches
@enum AXIS X=1 Y=2 Z=3


type Face
  axis::AXIS
  hi::Bool

  Face(a,h) = new(a,h)
  Face(a::Int,h::Bool) = new(AXIS(a),h)
end


type Continuation{T}
  segid::T
  voxels::Array{Int,2}
  overlaps::Dict 
  face::Face
  num_voxels::Int
  location::Tuple{Int,Int,Int}

  Continuation() = new(0,zeros(Int,(0,3)),Dict{Int,Int}(),Face(X,false),0,(0,0,0))
  Continuation(s,v,f) = new(s,v,Dict{Int,Int}(),f,0,(0,0,0))
  Continuation(s,v,o,f,n,l) = new(s,v,o,f,n,l)
end


Base.eltype{T}(c::Continuation{T}) = T


get_segid(c::Continuation) = c.segid
get_voxels(c::Continuation) = c.voxels
get_overlaps(c::Continuation) = c.overlaps
get_loc(c::Continuation) = c.location


set_size!(c::Continuation, s::Int) = c.num_voxels = s
set_loc!(c::Continuation, l::Tuple{Int,Int,Int}) = c.location = l
push_overlap!(c::Continuation, k, v) = push!(c.overlaps, k => v)
push_overlap!(c::Continuation, p::Pair) = push!(c.overlaps, p)

"""

    find_new_continuations{T}( seg::Array{T,3} )

  Traverses a segment volume over each of its faces might contact
  another chunk, and forms new Continuations where it finds them.
"""
function find_new_continuations{T}(seg::Array{T,3})

  continuations = Vector{Continuation{T}}();

  for axis in 1:3, hi_face in (true,false)

    new_continuations = find_face_continuations(seg, axis, hi_face)

    append!(continuations, new_continuations)

  end

  continuations
end


"""

    find_face_continuations{T}(seg::Array{T,3}, axis, hi_face::Bool)

  Finds the continuations within a particular face of the volume
"""
function find_face_continuations{T}(seg::Array{T,3}, axis::Int, hi_face::Bool)

  sx,sy,sz = size(seg)

  idxes = Vector(3)
  idxes[1] = 1:sz; idxes[2] = 1:sy; idxes[3] = 1:sz

  if hi_face    idxes[axis] = (idxes[axis]).stop
  else          idxes[axis] = 1
  end

  bvs = findvals_at_indices(seg, idxes)

  continuations = Vector{Continuation{T}}();

  for (segid,voxels) in bvs

    c = Continuation{T}( segid, voxels, Face(axis, hi_face) )

    push!(continuations,c)
  end

  continuations
end


"""

    findvals_at_indices{T}(seg::Array{T,3}, idxes)

  Traverses a volume using the `Union{Range,Int,Colon}` array `idxes`,
  and records where nonzero values exist. Returns a mapping from nonzero
  value to its voxels within the indices.
"""
function findvals_at_indices{T}(seg::Array{T,3}, idxes)

  locs = Dict{T,Vector{Vector{Int}}}();

  zT = T(0)
  for z in idxes[3], y in idxes[2], x in idxes[1]

    segid = seg[x,y,z]
    if segid == zT  continue  end

    if !haskey(locs,segid)  locs[segid] = []  end

    push!(locs[segid],[x,y,z])

  end

  #formatting as 2D Array
  Dict( k => [ loc[i] for loc in v, i in 1:3 ] for (k,v) in locs )
end


end #module Basic
