module Basic
#Common functions for EdgeFinders
#
# It can be time consuming, annoying, and disorganized to write several distinct
# variations for how to find edges. EdgeFinder classes are meant to abstract this
# process by wrapping a function for finding edges and allowing the user to
# specify all the required arguments by writing few extra functions and a
# dict of parameters.


using ...Types
using ...SegUtils
using ...Consolidation
using ...Chunking


export findedges, filteredges
export assign_aux_params!, assign_aux_vols!
export make_ccs!, get_ccs, compute_cc_stats, cc_bboxes
export filter_by_size!, filter_by_id!, dilate_ccs!
export findcontinuations


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
  pair processing occurs.
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

    assert_specified(ef::EdgeFinder, argname)

  Asserts a single EFarg has been properly specified. Less efficient
  than assert_specified for the entire set of arguments
"""
function assert_specified(ef::EdgeFinder, argname)

  T = filter( x -> x.name == argname, ef.reqs )[1].T

  @assert haskey( ef.args, argname ) "No $argname specified"
  @assert typeof(ef.args[argname]) <: T "Improper $argname specified"

end


"""

    make_ccs!{T}(ef::EdgeFinder, T=Int)

  All edge finders (so far) require connected components formed over the network
  output. This runs connected components, and fills in the corresponding volumes
  as arguments to the edge finder.
"""
function make_ccs!(ef::EdgeFinder, T=Int)

  assert_specified(ef, :PSDvol) 
  assert_specified(ef, :CCthresh)

  psdvol = ef.args[:PSDvol]
  cc_thr = ef.args[:CCthresh]


  ccs = zeros(T,size(psdvol))
  ccs = SegUtils.connected_components3D!( psdvol, view(ccs,:,:,:), cc_thr)

  ef.args[:ccs] = ccs
end


"""

    findcontinuations(ef::EdgeFinder)

  Finds the segments which continue to the next volume. Returns a
  list of Continuations (see Consolidation module for more details).
"""
function findcontinuations(ef::EdgeFinder)

  assert_specified(ef, :ccs)

  ccs = ef.args[:ccs]

  Consolidation.find_new_continuations(ccs)
end


"""

    findedges(ef::EdgeFinder)

  Default "NotImplementedError" for different edge finder types
"""
function findedges(ef::EdgeFinder)
  error("findedges not implemented for type $(typeof(ef))")
end


"""

    filteredges(ef::EdgeFinder, es)

  Default implementation
"""
filteredges(ef::EdgeFinder, es::Dict) = es


"""

    compute_cc_stats(ef::EdgeFinder)

  Computes the locations and sizes of `ef`'s connected components 
"""
function compute_cc_stats(ef::EdgeFinder)

  assert_specified(ef, :ccs)

  ccs = ef.args[:ccs]

  locs  = SegUtils.centers_of_mass(ccs)
  sizes = SegUtils.segment_sizes(ccs)

  locs, sizes
end



"""

    filter_by_size!(ef::EdgeFinder, sizes [, to_keep])

  Removes the connected components within the volume which are less
  than the size threshold (which should be specified as an aux arg before
  this step).

  If `to_keep` is specified, these extra values are preserved. This is useful
  for multiple chunk processing, as some segments can span multiple chunks.
"""
function filter_by_size!(ef::EdgeFinder, sizes, to_keep::Set=Set{Integer}())

  assert_specified(ef, :ccs)
  assert_specified(ef, :SZthresh)

  ccs = ef.args[:ccs]
  thr = ef.args[:SZthresh]


  over_thresh = Set(keys( filter( (k,v) -> v > thr, sizes ) ))
  
  if length(to_keep) > 0  union!(over_thresh, to_keep)  end

  filter_by_id!(ef, over_thresh)

end


"""

    filter_by_id!(ef::EdgeFinder, to_keep::Set{Integer})

  Sometimes, an edge finding scheme will need to tinker with this.
"""
function filter_by_id!(ef::EdgeFinder, to_keep::Set)

  assert_specified(ef, :ccs)

  ccs = ef.args[:ccs]

  SegUtils.filter_segs_by_id!(ccs, to_keep)

end


"""

    dilate_ccs!(ef::EdgeFinder)

  Dilates the ccs by the amount specified by the dilation argument
"""
function dilate_ccs!(ef::EdgeFinder)

  assert_specified(ef, :ccs)
  assert_specified(ef, :dilation)

  dil_ccs = copy(ef.args[:ccs])
  dilation = ef.args[:dilation]

  SegUtils.dilate_by_k!(dil_ccs, dilation)

  ef.args[:dil_ccs] = dil_ccs

end


"""

    get_ccs(ef::EdgeFinder)

  Extracts the relevant connected components
"""
function get_ccs(ef::EdgeFinder)

  assert_specified(ef, :ccs)

  copy(ef.args[:ccs])
end


"""

    find_focal_points(ef::EdgeFinder, seg, edges)

  Extracts points for which the each dilated segment overlaps
  with it's pre and post synaptic segment (specified by edges).
"""
function find_focal_points(ef::EdgeFinder, seg, edges)

  assert_specified(ef, :dil_ccs)

  dil_ccs = ef.args[:dil_ccs]

  SegUtils.find_focal_points(dil_ccs, seg, edges)
end


"""
Returns the bounding boxes for each segment within a volume
as a vector [xmin,ymin,zmin, xmax,ymax,zmax]
"""
function cc_bboxes(ef::EdgeFinder)

  assert_specified(ef, :ccs)

  ccs = ef.args[:ccs]

  Chunking.seg_bboxes(ccs)
end


end #module EF
