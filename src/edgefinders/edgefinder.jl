module EF
#Common functions for EdgeFinders
#
# It can be time consuming, annoying, and disorganized to write several distinct
# variations for how to find edges. EdgeFinder classes are meant to abstract this
# process by wrapping a function for finding edges and allowing the user to
# specify all the required arguments by writing few extra functions and a
# dict of parameters.


using ...Types


export assert_specified, findedges, filteredges
export assign_aux_params!, assign_aux_vols!, assign_ccs!
export get_ccs


#Specifying an enumeration for where we should look for the argument
# VOL => Should be explicitly passed (PSDsegs or MORPHsegs) -> assign_vols!
# SUBVOL => Should be a subvolume of the network output -> assign_aux_vols!
# AUX_PARAM => Should be an argument in the parameters dict -> assign_param!
@enum ARGTYPE VOL=1 SUBVOL=2 AUX_PARAM=3


type EFArg
  name :: Symbol
  T :: DataType
  argtype :: ARGTYPE
end


"""

    assign_aux_params!(ef::EdgeFinder, params::Dict)

EdgeFinders often require some extra information to run from the user-specified
parameters. This fills those in.
"""
function assign_aux_params!(ef::EdgeFinder, params::Dict)

  for arg in ef.reqs
    if arg.argtype == AUX_PARAM
      ef.args[arg.name] = params[arg.name]
    end
  end

end


"""

    assign_aux_vols!{T}(ef::EdgeFinder, net_output::Array{T,4}, volume_map::Dict)

  Some edge finders require auxiliary volumes from the network output. This
  function fills those spots with views from the network output
"""
function assign_aux_vols!{T}(ef::EdgeFinder, net_output::Array{T,4}, seg::Array,
                            volume_map::Dict)

  for arg in ef.reqs
    if arg.argtype == SUBVOL
      vol_i = volume_map[arg.name]
      ef.args[arg.name] = view( net_output,:,:,:,vol_i )
    end
  end

  #always required
  ef.args[:MORPHsegs] = view(seg,:,:,:)

end


"""

    assert_specified(ef::EdgeFinder)

  Asserts that the required volumes have been filled in before
  any processing occurs.
"""
function assert_specified(ef::EdgeFinder)

  for arg in ef.reqs
    @assert haskey( ef.args, arg.name )
    # debug
    # println("supplied: $(typeof(ef.args[arg.name])), reqd: $(arg.T)")
    @assert typeof(ef.args[arg.name]) <: arg.T
  end

end


"""

    assign_ccs!{T}(ef::EdgeFinder, T=Int)

  All edge finders (so far) require connected components formed over the network
  output. This runs connected components, and fills in the corresponding volumes
  as arguments to the edge finder.
"""
function assign_ccs!(ef::EdgeFinder, T=Int)
  error("assign_ccs! not implemented for type $(typeof(ef))")
end


"""

    find_edges(ef::EdgeFinder)

  Default "NotImplementedError" for different edge finder types
"""
function findedges(ef::EdgeFinder)
  error("findedges not implemented for type $(typeof(ef))")
end


"""

    filter_edges(ef::EdgeFinder, es)

  Default implementation
"""
filteredges(ef::EdgeFinder, es::Dict) = es


"""
"""
function get_ccs(ef::EdgeFinder)
  error("get_ccs not implemented for type $(typeof(ef))")
end

end #module EF
