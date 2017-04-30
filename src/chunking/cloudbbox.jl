module CloudBBoxes
#Extensions of bbox interface for types used in large/cloud applications

using BigArrays
#unfortunately, I need to write these so they're the most specific
# or at least, I don't know a way around this
function Base.getindex(a::BigArray, bbox::BBox)

  indices = Vector{Any}(length(size(a)))
  indices[:] = Colon()

  indices[1] = bbox.f.x:bbox.l.x
  indices[2] = bbox.f.y:bbox.l.y
  indices[3] = bbox.f.z:bbox.l.z

  a[indices...]
end


function Base.getindex(a::BigArray, bbox::BBox, I...)

  indices = Vector{Any}(length(size(a)))
  indices[:] = Colon()

  indices[1] = bbox.f.x:bbox.l.x
  indices[2] = bbox.f.y:bbox.l.y
  indices[3] = bbox.f.z:bbox.l.z

  for (i,v) in enumerate(I)  indices[3+i] = v  end

  a[indices...]
end


function Base.setindex!(a::BigArray, X, bbox::BBox)

  indices = Vector{Any}(length(size(a)))
  indices[:] = Colon()

  indices[1] = bbox.f.x:bbox.l.x
  indices[2] = bbox.f.y:bbox.l.y
  indices[3] = bbox.f.z:bbox.l.z

  a[indices...] = X
end


function Base.setindex!(a::BigArray, X, bbox::BBox, I...)

  indices = Vector{Any}(length(size(a)))
  indices[:] = Colon()

  indices[1] = bbox.f.x:bbox.l.x
  indices[2] = bbox.f.y:bbox.l.y
  indices[3] = bbox.f.z:bbox.l.z

  for (i,v) in enumerate(I)  indices[3+i] = v  end

  a[indices...] = X
end


end #module BBoxes
