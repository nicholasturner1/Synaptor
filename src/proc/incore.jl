
module InCore


using ...Types
using ...EdgeFinders
using ..Utils


export process_single_chunk


function process_single_chunk( chunk, seg, ef::EdgeFinder ; params...)

  params = Utils.collect_params(params)

  EdgeFinders.assign_aux_params!(ef, params)

  EdgeFinders.assign_aux_vols!(ef, chunk, seg, params[:volume_map])

  EdgeFinders.assign_ccs!(ef)

  EdgeFinders.findedges(ef)
end


end #module InCore
