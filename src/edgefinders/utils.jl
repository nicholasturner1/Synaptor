module Utils
#Generalized utilities for edge finders


export find_pairs


"""

    find_pairs( spmat::SparseMatrixCSC )

  `findn` that returns a list of tuples
"""
function find_pairs( spmat::SparseMatrixCSC )
  f = findn(spmat)
  collect(zip(f[1],f[2]))
end


"""

    extract_unique_rows

  Finds the unique row indices of a sparse matrix
"""
extract_unique_rows( overlap::SparseMatrixCSC ) = unique(findn(overlap)[1])


"""

    split_map_into_groups( segmap::Dict, ids )

  Takes a mapping from segment ids to groups, as well as a list of groups,
  and separates the segment ids into lists depending upon their group
  membership. This ignores segments mapped to groups other than those
  listed in `ids`
"""
function split_map_into_groups( segmap::Dict, ids )

  groups = [ Vector{Int}() for i in ids ]

  for (k,v) in segmap
    for i in eachindex(ids)
      if v == group_ids[i] push!( groups[i], k ) end
    end
  end

  groups
end


end #module Utils
