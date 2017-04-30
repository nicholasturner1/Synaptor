module ConsolidateFocalPoints

export consolidate_focal_points

function consolidate_focal_points( chunk_focal_pts::Array )

  res = Dict{Int,Tuple{Tuple{Int,Int,Int},Tuple{Int,Int,Int}}}()

  empty_val = (-1,-1,-1)
  #randomizing the order selects from overlapping ids randomly
  for fp in shuffle(chunk_focal_pts), (k,v) in fp

    if !haskey(res,k)  
      res[k] = v  
      continue  
    end
    
    if !(empty_val in res[k])  continue  end

    old_val = res[k]
    new_val = old_val
    if old_val[1] == empty_val  new_val = (v[1], new_val[2])  end
    if old_val[2] == empty_val  new_val = (new_val[1], v[2])  end

    res[k] = new_val
  end

  res
end

end #module ConsolidateFocalPoints
