module EF
#Common functions for EdgeFinders


using ...Types


export assign_volumes!, assert_specified, find_edges


#Specifying an enumeration for where we should look for the argument
# VOL => Should be explicitly passed (PSDsegs or MORPHsegs) -> assign_vols!
# SUBVOL => Should be a subvolume of the network output -> assign_aux_vols!
# AUX_PARAM => Should be an argument in the parameters dict -> assign_param!
@enum ARGTYPE VOL=1 SUBVOL=2 AUX_PARAM=3


type EFArg
  name :: String
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
function assign_aux_vols!{T}(ef::EdgeFinder, net_output::Array{T,4},
                            volume_map::Dict)

  for arg in ef.reqs
    if arg.argtype == SUBVOL
      vol_i = volume_map[arg.name]
      ef.args[arg.name] = view( net_output,:,:,:,vol_i )
    end
  end

end


"""

    assign_ccs!{T}(ef::EdgeFinder, net_output::Array{T,4}, volume_map::Dict)

  All edge finders (so far) require connected components formed over the network
  output. This runs connected components, and fills in the corresponding volumes
  as arguments to the edge finder.
"""
function assign_ccs!(ef::EdgeFinder, psdsegs::Array, seg::Array, params::Dict)
  #NOTE INCOMPLETE
  0#stub
end



"""

    assert_specified(ef::EdgeFinder)

  Asserts that the required volumes have been filled in before
  any processing occurs.
"""
function assert_specified(ef::EdgeFinder)

  for arg in ef.reqs
    @assert haskey( ef.args, arg.name )
    @assert ef.args[arg.name] <: arg.T
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
