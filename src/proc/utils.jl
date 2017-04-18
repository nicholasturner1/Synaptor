module Utils

export collect_params
export create_range_grid


collect_params(p) = Dict( name => val for (name,val) in p )


"""
Removes dictionary entries which are not contained under `keys_to_keep`
"""
function filter_by_id!(keys_to_keep, dicts::Dict...)

  for d in dicts  filter!( (k,v) -> k in keys_to_keep, d)  end

end


function create_range_grid(params)

  range_params = filter( (k,v) -> typeof(v) <: Range, params )

  @assert length(range_params) > 0

  range_names = collect(keys(range_params))
  ordered_ranges = [collect(range_params[name]) for name in range_names]
  range_lengths = map(length, ordered_ranges)

  range_grid = Array{Dict}(range_lengths...)

  grid_sz = size(range_grid)
  num_ranges = length(grid_sz)
  for i in eachindex(range_grid)
    sub = ind2sub(grid_sz, i)

    range_vals = [ ordered_ranges[j][k] for (j,k) in enumerate(sub) ]
    range_grid[i] = Dict( name => val
                          for (name,val) in zip(range_names, range_vals) )
  end

  range_grid, range_names
end


end #module Utils
