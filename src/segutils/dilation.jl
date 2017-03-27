module Dilation

export dilate_by_k!


"""

    dilate_by_k!( d, k )

  Dilates the segments within d by k
  in 2D manhattan distance
"""
function dilate_by_k!( d, k )

  md = manhattan_distance2D!(d)

  for i in eachindex(d)
    if md[i] > k
      d[i] = eltype(d)(0)
    end
  end

end


"""

    manhattan_distance2D!( d )

  Performs a 2D manhattan distance transformation over
  a 3D volume inplace.
"""
function manhattan_distance2D!{T}( d::AbstractArray{T,3} )

  restype = UInt32
  maxx, maxy, maxz = size(d)
  dists = zeros(restype, size(d))

  for k in 1:maxz
    for j in 1:maxy
      for i in 1:maxx

        if  d[i,j,k] > T(0)
           dists[i,j,k] = 0
        else
           dists[i,j,k] = typemax(restype)
        end

        if i>1  &&  dists[i-1,j,k]+1 <= dists[i,j,k]
          dists[i,j,k] = dists[i-1,j,k]+1;
          d[i,j,k] = d[i-1,j,k];
        end
        if j>1  &&  dists[i,j-1,k]+1 <= dists[i,j,k]
          dists[i,j,k] = dists[i,j-1,k]+1;
          d[i,j,k] = d[i,j-1,k];
        end

        #for 3d case
        #if k>1  dists[i,j,k] = minimum(( dists[i,j,k], dists[i,j,k-1]+1 )) end

      end
    end
  end

  for k in maxz:-1:1
    for j in maxy:-1:1
      for i in maxx:-1:1

        if i<maxx  &&  dists[i+1,j,k]+1 <= dists[i,j,k]
          dists[i,j,k] = dists[i+1,j,k]+1;
          d[i,j,k] = d[i+1,j,k];
        end
        if j<maxy  &&  dists[i,j+1,k]+1 <= dists[i,j,k]
          dists[i,j,k] = dists[i,j+1,k]+1;
          d[i,j,k] = d[i,j+1,k];
        end
        #if k<maxz  dists[i,j,k] = minimum(( dists[i,j,k], dists[i,j,k+1]+1 )) end

      end
    end
  end

  dists
end


end#module Dilation
