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


end #module Utils
