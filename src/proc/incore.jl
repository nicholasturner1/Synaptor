module InCore


using ...Types
using ...EdgeFinders
using ...Continuations
using ..Utils


export process_chunk, process_chunk_w_continuations


function process_chunk( chunk, seg, ef::EdgeFinder ; params...)

  #Handling parameters
  params = Utils.collect_params(params)
  EdgeFinders.assign_aux_params!(ef, params)

  #Filling out basic EF requirements
  EdgeFinders.assign_aux_vols!(ef, chunk, seg, params[:volume_map])
  EdgeFinders.make_ccs!(ef)


  locs, sizes = EdgeFinders.compute_cc_stats(ef)


  EdgeFinders.filter_by_size!(ef, sizes)


  EdgeFinders.dilate_ccs!(ef) 


  edges, invalid, overlap = EdgeFinders.findpairs(ef)

  #Formatting & Cleaning results
  ccs = EdgeFinders.get_ccs(ef)
  to_keep_seg = Set(keys(edges))
  SegUtils.filter_by_id!(ccs, to_keep_seg)
  Utils.filter_by_id!(to_keep_seg, locs, sizes)


  edges, locs, sizes
end


function process_chunk_w_continuations( chunk, seg, ef::EdgeFinder; params... )

  #Handling parameters
  params = Utils.collect_params(params)
  EdgeFinders.assign_aux_params!(ef, params)

  #Filling out basic EF requirements
  EdgeFinders.assign_aux_vols!(ef, chunk, seg, params[:volume_map])
  EdgeFinders.make_ccs!(ef)
 

  continuations = EdgeFinders.find_continuations(ef) 
  locs, sizes = EdgeFinders.compute_cc_stats(ef)


  #Removing small segs which aren't continuations
  c_keys = Set(keys(continuations))
  EdgeFinders.filter_by_size!(ef, sizes, c_keys)


  EdgeFinders.dilate_ccs!(ef) 


  edges, invalid, overlap = EdgeFinders.findpairs(ef)
  Continuations.fill_overlaps!(continuations, overlap)


  #Formatting & Cleaning results
  complete_es = setdiff(Set(keys(edges)), c_keys)
  EdgeFinders.filter_by_id!(ef, union(complete_es, c_keys))
  Utils.filter_by_id!(complete_es, locs, sizes)


  edges, locs, sizes, continuations
end


end #module InCore
