#!/usr/bin/env julia

#=
  Masking Utilities - mask_u
=#

module mask_u


"""

    clip_polygon( pxs, pys, cxs, cys )

  Clips a subject polygon (specified by x coords pxs, and y's pys),
  by a convex clip polygon (cxs, cys) using the Sutherland-Hodgman
  algorithm. Vertices are assumed to be listed in counter-clockwise order
"""
function clip_polygon( pxs, pys, cxs, cys )

  @assert length(pxs) == length(pys)
  @assert length(cxs) == length(cys)

  ps = collect(zip(pxs,pys))
  cs = collect(zip(cxs,cys))
  rs = ps #result

  num_clip_verts = length(cs)

  ci = num_clip_verts #"source" vertex index
  for cj in 1:num_clip_verts #"dest" vertex index

    ips = rs #"inputList" vertices
    rs = Tuple[];

    num_subj_verts = length(ips)
    si = num_subj_verts #"source" subj index
    for sj in 1:num_subj_verts
      if isinside(ips[sj], cs[ci],cs[cj])

        if !isinside(ips[si], cs[ci],cs[cj])
          push!(rs, find_intersection(ips[si],ips[sj], cs[ci],cs[cj]))
        end
        push!(rs,ips[sj])

      elseif isinside(ips[si], cs[ci],cs[cj])
        push!(rs, find_intersection(ips[si],ips[sj], cs[ci],cs[cj]))
      end

      si=sj
    end
    ci=cj
  end

  @assert length(rs) > 0
  rxs, rys = zip(rs...)
  rxs, rys
end


"""

    isinside( p, src, dst )

  Determines whether a point is on the "inside" side of a line bounding
  a polygon. The polygon is specified by a source and destination point.
  If following a counter-clockwise vertex list convention, the "inside" corresponds
  to a positive cross product.
"""
@inline function isinside( p, src, dst )
  (dst[1]-src[1])*(p[2]-src[2])-(dst[2]-src[2])*(p[1]-src[1]) > 0
end


"""

    find_intersection( src1, dst1, src2, dst2 )

  Finds the intersection of two lines, each defined by a pair of points.
  Apparenty, this formula uses determinants, but I don't know how that works.
"""
function find_intersection( src1, dst1, src2, dst2 )
  diff1 = (src1[1]-dst1[1],src1[2]-dst1[2])
  diff2 = (src2[1]-dst2[1],src2[2]-dst2[2])

  numer_t1 = src1[1]*dst1[2] - src1[2]*dst1[1]
  numer_t2 = src2[1]*dst2[2] - src2[2]*dst2[1]

  denom = (src1[1]-dst1[1])*(src2[2]-dst2[2]) - (src1[2]-dst1[2])*(src2[1]-dst2[1])

  ((diff2[1]*numer_t1 - diff1[1]*numer_t2) / denom, #x
   (diff2[2]*numer_t1 - diff1[2]*numer_t2) / denom) #y
end


"""

    fill_polygon!{T}(vol::Array{T,2}, pxs, pys, v::T)

  Fills a volume with the value v whether the index is contained within
  a polygon (specified by pxs and pys).
"""
function fill_polygon!{T}( vol::AbstractArray{T,2}, pxs, pys, v::T, offset=Int[0,0] )

  @assert length(pxs) == length(pys)

  num_verts = length(pxs)

  sx,sy = size(vol)

  for y in 1:sy
    xs = [];
    j = num_verts
    y_w_off = y+offset[2]
    for i in eachindex(pys)
      if ((pys[i]>(y_w_off)) != (pys[j]>(y_w_off)))

        crossx = ((y_w_off-pys[i]) * (pxs[j]-pxs[i]) / (pys[j]-pys[i]) + pxs[i])
        push!(xs,crossx)
      end
      j = i
    end #i loop

    sort!(xs)

    #relating bounds to the current reference volume
    # (and shifting the indexing to be consistent across x and y
    map!(x -> round(Int,x)-offset[1], xs)
    for i in 2:2:length(xs) xs[i] -= 1 end
    xs = _filter_indices!(xs, (1,sx))

    for i in 1:2:length(xs)
      vol[xs[i]:xs[i+1],y] = v #-1 SHOULD acct for indexing scheme, but unsure
    end
  end #x loop

  vol
end


"""

    filter_indices(is, bounds)

  Modifies a list of indices which specify entry/exit points of a ray
  cast across a polygon in order to fit the passed bounds. The indices
  are assumed to be sorted.
"""
function _filter_indices!( is, bounds )

  st_b, end_b = bounds
  st_i, end_i = 1, length(is)

  if end_i == 0 return [] end
  if is[end] < st_b || is[1] > end_b return [] end

  @assert mod(length(is),2) == 0
  #while the "exit" point of the index range is
  # before the start point of the volume
  while st_b > is[st_i+1]
    st_i += 2
  end

  while end_b < is[end_i-1]
    end_i -= 2
  end

  is[st_i]  = max(st_b,is[st_i])
  is[end_i] = min(end_b,is[end_i])

  is[st_i:end_i]
end


"""

    fill_polygon_volume!{T}(vol::AbstractArray{T,3}, p_list, v::T, offset=Int[0,0])

  Fills a 3d volume according to the polygons specified in p_list. The number of polygons
  should be equal to the number of slices in z. The value v is placed into the volume
  whenever an index is contained within the polygon. Each polygon is specified as:

  ( \${list_of_x_coords}, \${list_of_y_coords} )
"""
function fill_polygon_volume!{T}( vol::AbstractArray{T,3}, p_list, v::T, offset=Int[0,0] )

  sx,sy,sz = size(vol)
  @assert length(p_list) == sz

  for z in 1:sz
    pxs, pys = p_list[z]
    fill_polygon!(view(vol,:,:,z),pxs,pys,v,offset)
  end

end


function polygon_volume_mask( vol_size, p_list, offset=Int[0,0] )

  mask = zeros(Bool,vol_size)
  fill_polygon_volume!(mask, p_list, true, offset)

  mask
end


function mask_vol_by_polygons!{T}( vol::AbstractArray{T,3}, p_list, offset=Int[0,0] )

  println("offset $offset")
  mask = polygon_volume_mask(size(vol), p_list, offset)
  # println(unique(mask))

  zT = eltype(vol)(0)
  count=0
  for i in eachindex(mask)
    if mask[i] continue end
    count += 1
    vol[i] = zT
  end

  println("$count voxels masked")

end


function polygon_list( p_struct, start_index, list_length )

  println("polygon list start: $start_index list_length: $list_length")

  index_range = start_index:(start_index+list_length-1)

  [p_struct[i] for i in index_range]
end

"""

    poly2mask( pxs, pys, m, n, T=Bool )

  Creates an m x n  mask which specified the indices within a
  polygon (specified by pxs and pys)
"""
function poly2mask( pxs, pys, m, n, offset=[0,0], T=Bool )
  mask = zeros(T,m,n)
  fill_polygon!(mask, pxs, pys, one(T), offset)
  mask
end


"""

    in_polygon( x, y, pxs, pys )

  Tests whether a point (x,y) is contained within the polygon
  specified by pxs and pys
"""
function in_polygon( x, y, pxs, pys )

  @assert length(pxs) == length(pys)
  num_verts = length(pxs)

  contained = false
  j = num_verts
  for i in 1:num_verts

    if ( ((pys[i]>y) != (pys[j]>y)) && #crosses y coordinate
         #on right (pos x) side
         x < ((pxs[j] - pxs[i]) * (y-pys[i]) / (pys[j]-pys[i]) + pxs[i])
       )
      contained = !contained
    end
    j = i
  end

  contained
end


"""

    consolidated_polygons( p_dict, window_radius )

  Forms a list of polygons equal to the length of p_list where
  each polygon is the intersection of itself with all the other
  polygons within some radius of itself
"""
function consolidated_polygons( p_dict, window_radius, window_bounds)

  num_ps = length(p_dict)

  consolidated_ps = Dict();
  for (k,v) in p_dict
    p_window = [p_dict[i] for i in _index_window(k,window_radius,window_bounds)]

    p_i = p_window[1]
    for i in 1:length(p_window)
      p_i = clip_polygon(p_i[1],p_i[2],p_window[i][1],p_window[i][2])
    end

    consolidated_ps[k] = p_i
  end

  consolidated_ps
end


"""

    index_window(i,r,bounds)

  Finds the range of all indices between the end points of
  bounds and within distance r of i
"""
@inline function _index_window(i,r, bounds)
  max(i-r+1,bounds[1]):min(i+r-1,bounds[2])
end


end #module
