module BBoxes


export BBox


immutable Vec3
  x::Int
  y::Int
  z::Int

  Vec3(x,y,z) = new(x,y,z)
  Vec3(s::Real) = new(s,s,s)
  Vec3(v) = new(v[1],v[2],v[3])
end


Base.:(+)(a::Vec3, b::Vec3) = Vec3(a.x + b.x, a.y + b.y, a.z + b.z)
Base.:(-)(a::Vec3, b::Vec3) = Vec3(a.x - b.x, a.y - b.y, a.z - b.z)

Base.:(+)(a::Vec3, s::Real) = Vec3(a.x + s, a.y + s, a.z + s)
Base.:(-)(a::Vec3, s::Real) = Vec3(a.x - s, a.y - s, a.z - s)
Base.:(+)(s::Real, a::Vec3) = a + s
Base.:(-)(s::Real, a::Vec3) = Vec3(s - a.x, s - a.y, s - a.z)

Base.:(*)(a::Vec3, s::Real) = Vec3(a.x * s, a.y * s, a.z * s)
Base.:(/)(a::Vec3, s::Real) = Vec3(a.x / s, a.y / s, a.z / s)
Base.:(*)(s::Real, a::Vec3) = a * s
Base.:(/)(s::Real, a::Vec3) = Vec3(s / a.x, s / a.y, s / a.z)

Base.min(v1::Vec3,v2::Vec3) = Vec3(min(v1.x,v2.x), min(v1.y,v2.y), min(v1.z,v2.z))
Base.max(v1::Vec3,v2::Vec3) = Vec3(max(v1.x,v2.x), max(v1.y,v2.y), max(v1.z,v2.z))

collect(a::Vec3) = [a.x, a.y, a.z]
Base.show(io::IO, v::Vec3) = print(io, "($(v.x),$(v.y),$(v.z))")


immutable BBox
  f::Vec3
  l::Vec3


  BBox(f::Vec3,l::Vec3) = new(f,l)
  BBox(x1,y1,z1,x2,y2,z2) = new(Vec3(x1,y1,z1),Vec3(x2,y2,z2))
  BBox(v1,v2) = new(Vec3(v1[1],v1[2],v1[3]),Vec3(v2[1],v2[2],v2[3]))

  function BBox(p::Pair)
    x1,y1,z1 = p.first
    x2,y2,z2 = p.second

    BBox(x1,y1,z1,x2,y2,z2)
  end

  BBox(d::AbstractArray) = new(Vec3(1,1,1),Vec3(size(d)))
  BBox(d::AbstractArray, offset) = BBox(d) + offset
end

Base.first(bbox::BBox) = bbox.f
Base.last(bbox::BBox)  = bbox.l

Base.:(+)(bbox::BBox, v::Vec3) = BBox(bbox.f+v, bbox.l+v)
Base.:(-)(bbox::BBox, v::Vec3) = BBox(bbox.f-v, bbox.l-v)
Base.:(+)(bbox::BBox, v) = bbox + Vec3(v)
Base.:(-)(bbox::BBox, v) = bbox - Vec3(v)

Base.:(&)(b1::BBox, b2::BBox) = BBox(max(b1.f,b2.f),min(b1.l,b2.l))

Base.show(io::IO, bbox::BBox) = print(io, "BBox{$(bbox.f)<->$(bbox.l)}")
Base.size(bbox::BBox) = bbox.l - bbox.f + 1


@inline function Base.getindex{T}(a::AbstractArray{T,3}, bbox::BBox)
  a[bbox.f.x:bbox.l.x,
    bbox.f.y:bbox.l.y,
    bbox.f.z:bbox.l.z]
end


function Base.getindex{T,N}(a::AbstractArray{T,N}, bbox::BBox)
  
  indices = Vector{Any}(N)
  indices[:] = Colon()

  indices[1] = bbox.f.x:bbox.l.x
  indices[2] = bbox.f.y:bbox.l.y
  indices[3] = bbox.f.z:bbox.l.z

  a[indices...]
end


function Base.getindex{T,N}(a::AbstractArray{T,N}, bbox::BBox, I...)

  indices = Vector{Any}(N)
  indices[:] = Colon()

  indices[1] = bbox.f.x:bbox.l.x
  indices[2] = bbox.f.y:bbox.l.y
  indices[3] = bbox.f.z:bbox.l.z

  for (i,v) in enumerate(I)  indices[3+i] = v  end

  a[indices...]
end


end #module BBoxes
