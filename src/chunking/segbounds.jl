module SegBounds

using ..BBoxes

export seg_bboxes

function seg_bboxes{T}( seg::AbstractArray{T} )

  bboxes = Dict{T,BBox}();

  sx,sy,sz = size(seg)

  zT = T(0)
  maxint = typemax(Int); minint = typemin(Int)
  locmax = BBoxes.Vec3(maxint, maxint, maxint)
  locmin = BBoxes.Vec3(minint, minint, minint)

  for z in 1:sz, y in 1:sy, x in 1:sx

    if seg[x,y,z] == 0  continue  end

    segid = seg[x,y,z]
    curr_box = get(bboxes, segid, BBox(locmax,locmin))

    bboxes[segid] = BBox(min(curr_box.f,(x,y,z)),
                         max(curr_box.l,(x,y,z)))
  end

  bboxes
end


end #module SegBounds
