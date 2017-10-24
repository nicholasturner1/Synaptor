module DilComps

using ..ConnComps
using ..Dilation

export dilated_components, dilated_components!


function dilated_components{T}( d::AbstractArray{T}, dil_param=0,
                                cc_thresh=zero(T) )

  res = zeros( Int, size(d) )

  dilated_components!( d, res, dil_param, cc_thresh )
end


function dilated_components!{S,T}( d::AbstractArray{S}, res::AbstractArray{T},
                                 dil_param=0, cc_thresh=zero(S) )

  #thresholding
  threshT = eltype(d)(cc_thresh); oT = T(1)
  for (i,v) in enumerate(d)
    if v > threshT  res[i] = oT  end
  end

  if dil_param > 0  Dilation.dilate_by_k!(res, dil_param)  end

  res = connected_components3D!(res, res)

  if dil_param > 0
    #Removing dilated voxels
    for (i,v) in enumerate(d)
      if v <= threshT  res[i] = 0  end
    end
  end

  res
end


end #module DilComps
