module EF
#Common functions for EdgeFinders


using ...Types


export assign_volumes!, assert_specified, find_edges


"""

    assign_volumes!{T}(ef::EdgeFinder, net_output::Array{T,4},
                       volume_map::Dict{AbstractString,Integer})

  Pre-fills the "arguments" of the edge finder according to the
  volume map specified by the user.
"""
function assign_volumes!{T}(ef::EdgeFinder, net_output::Array{T,4},
                            volume_map::Dict)

  for vol_name in ef.reqd_vol_names
    vol_i = volume_map[vol_name]
    ef.reqd_vols[vol_name] = view( net_output,:,:,:,vol_i )
  end

end


"""

    assert_specified(ef::EdgeFinder)

  Asserts that the required volumes have been filled in before
  any processing occurs.
"""
function assert_specified(ef::EdgeFinder)

  for vol_name in ef.reqd_vol_names
    @assert haskey( ef.reqd_vols, vol_name )
  end

end


"""

    find_edges(ef::EdgeFinder)

  Default "NotImplementedError" for different edge finder types
"""
function find_edges(ef::EdgeFinder)
  error("find_edges not implemented for type $(typeof(ef))")
end

end #module EF
