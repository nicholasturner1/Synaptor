module Basic
# Continuations represent segments which could pass onto the next
# chunk in a dataset which is too large to fit in RAM
#
# In order to properly specify a continuation, we need to know
# which face it contacts within a 3d chunk of data. The AXIS and
# Face classes help to specify that information.


#Classes
export Continuation, AXIS, Face
#Faces
export get_axis, get_hi, opposite 
#Continuations
export get_segid, get_voxels, get_overlaps, get_loc, get_face, get_num_voxels
export set_size!, set_loc!, push_overlap!


#================
CLASS DEFINITIONS: AXIS, Face

#Describing which face the continuation touches
================#

@enum AXIS X=1 Y=2 Z=3


immutable Face
  axis::AXIS
  hi::Bool

  Face(a,h) = new(a,h)
  Face(a::Int,h::Bool) = new(AXIS(a),h)
end

#================
Face Fns
================#

get_axis(f::Face) = Int(f.axis)
get_hi(f::Face) = f.hi
opposite(f::Face) = Face(f.axis, !f.hi)

#================
CLASS DEFINITIONS: Continuation
================#

type Continuation
  segid::Int
  voxels::Array{Int,2}
  overlaps::Dict 
  face::Face
  num_voxels::Int
  location::Vector{Int}

  Continuation() = new(0,zeros(Int,(0,3)),Dict{Int,Int}(),Face(X,false),0,[0,0,0])
  Continuation(s::Int,v::Array,f::Face) = new(s,v,Dict{Int,Int}(),f,0,[0,0,0])
  Continuation(s,v,o,f,n,l) = new(s,v,o,f,n,l)
  Continuation(o::Dict,n::Int,l::Vector) = new(0,zeros(Int,(0,3)),o,Face(X,false),n,l)
end


#================
Continuation Fns
================#


get_segid(c::Continuation) = c.segid
get_voxels(c::Continuation) = c.voxels
get_overlaps(c::Continuation) = c.overlaps
get_loc(c::Continuation) = c.location
get_face(c::Continuation) = c.face
get_num_voxels(c::Continuation) = c.num_voxels

function Base.show(io::IO, c::Continuation)
  print(io, "Continuation{segid:$(c.segid), loc:$(c.location), #vox:$(c.num_voxels)}")
end


set_size!(c::Continuation, s::Int) = c.num_voxels = s
set_loc!(c::Continuation, l::Tuple{Int,Int,Int}) = c.location = l
set_overlaps!(c::Continuation, o::Dict) = c.overlaps = o
push_overlap!(c::Continuation, k, v) = push!(c.overlaps, k => v)
push_overlap!(c::Continuation, p::Pair) = push!(c.overlaps, p)

""" Merging two continuations together """
function Base.:+(c1::Continuation, c2::Continuation)
  new_overlaps = sum_dicts(c1.overlaps, c2.overlaps)
  new_num_voxels = c1.num_voxels + c2.num_voxels
  new_loc = avg_locations(c1.location, c2.location, c1.num_voxels, c2.num_voxels)

  Continuation(new_overlaps, new_num_voxels, new_loc)
end


function sum_dicts{S,T}(d1::Dict{S,T}, d2::Dict{S,T})

  k1 = Set(keys(d1))
  k2 = Set(keys(d2))
  all_keys = union(k1,k2)

  res = Dict{S,T}();

  for k in all_keys
    if k in k1 && k in k2  res[k] = d1[k] + d2[k]
    elseif k in k1         res[k] = d1[k]
    elseif k in k2         res[k] = d2[k]
    end
  end

  res
end


avg_locations(l1::Vector, l2::Vector, n1, n2) = round(Int,(((l1*n1)+(l2*n2))/(n1+n2)))


#================
Related Utility Fns
================#

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


function fill_overlaps!(c_list::Vector{Continuation}, overlap::SparseMatrixCSC)

  segids = Set([ get_segid(c) for c in c_list ])

  segid_to_overlaps = Dict{Int,Dict{Int,Int}}();

  for segid in segids
    segid_to_overlaps[segid] = overlap_row_dict(overlap, segid)
  end

  for c in c_list
    set_overlaps!(c, segid_to_overlaps[ get_segid(c) ])
  end

end


function overlap_row_dict(overlaps::SparseMatrixCSC, rowid)

  res = Dict{Int,Int}()

  rows = rowvals(overlaps)
  vals = nonzeros(overlaps)

  for i in 1:size(overlaps,2)
    for j in nzrange(overlaps,i)

      r = rows[j]
      if r != rowid  continue  end

      val = vals[j]
      res[i] = val
    end
  end

  res
end


end #module Basic
