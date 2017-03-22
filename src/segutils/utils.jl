
module Utils
#all other misc segmentation utils

export relabel_data!, relabel_data
export centers_of_mass


function relabel_data!{T}( d::AbstractArray{T}, mapping )

  zT = zero(T)
  for i in eachindex(d)
    
    if d[i] == zT continue end

    v = d[i]
    d[i] = get( mapping, v, v );
  end

end


function relabel_data{T}( d::AbstractArray{T}, mapping )

  s = size(d)
  res = zeros(T, s)

  zT = zero(T)
  for i in eachindex(d)

    if d[i] == zT continue end

    d[i] = get( mapping, v, v );
  end

  res
end


function centers_of_mass{T}( d::AbstractArray{T} )

  coms = Dict{T,Vector}()
  sizes = Dict{T,Int}()

  sx,sy,sz = size(d)
  zT = zero(T)
  for k in 1:sz, j in 1:sy, i in 1:sx

    if d[i,j,k] == zT continue end
    segid = d[i,j,k]

    coms[segid]  = get( coms, segid, [0,0,0]) + [i,j,k]
    sizes[segid] = get( sizes, segid, 0) + 1
  end

  for k in keys(coms)
    coms[k] = round(Int, coms[k] / sizes[k])
  end

  coms
end


end #module Utils
