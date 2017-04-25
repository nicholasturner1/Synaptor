module ConsolidateIDs

export consolidate_ids, consolidate_edge_dict, apply_id_maps


function consolidate_edge_dict{T}( dict_arr::Array{Dict{Int,T}} )

  key_arr = map( x -> Set(keys(x)), dict_arr )

  id_maps = consolidate_ids(key_arr)

  apply_id_maps(dict_arr, id_maps)
end


function consolidate_ids( id_arr )

  taken_ids = Set{Int}();
  id_maps = Array{Dict{Int,Int}}( size(id_arr) );
  for i in eachindex(id_maps)  id_maps[i] = Dict{Int,Int}()  end

  next_id = 1
  for (i,curr_ids) in enumerate(id_arr)
    for id in curr_ids

      if !(id in taken_ids)
        push!(taken_ids, id)
        id_maps[i][id] = id

      else
        while next_id in taken_ids  next_id += 1  end
        push!(taken_ids, next_id)
        id_maps[i][id] = next_id

      end
    end
  end

  id_maps
end


function apply_id_maps( dict_arr::Array{Dict}, id_maps::Array{Dict{Int,Int}} )

  consolidated_dict = Dict()

  for (i,d) in enumerate(dict_arr), (k,v) in d
    consolidated_dict[id_maps[i][k]] = v
  end

  consolidated_dict
end

end #module ConsolidateIDs
