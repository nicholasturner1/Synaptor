module SemanticEF


using ...Types
using ..EF


export SemanticEdgeFinder, find_edges


required_volume_names = ["PSDSegs","MorphSegs","Axon","Dendrite"]
optional_volume_names = ["Glia"] #not implemented yet


type SemanticEdgeFinder <: EdgeFinder
  reqd_vol_names :: Array{String}
  reqd_vols :: Dict{String,Array}

  SemanticEdgeFinder() = new(required_volume_names, Dict{String,Array}())
end


function EF.find_edges(ef::SemanticEdgeFinder)

  EF.assert_specified(ef)

  axon_vol = ef.reqd_vols["Axon"]
  dend_vol = ef.reqd_vols["Dendrite"]
  psd_vol  = ef.reqd_vols["PSD"]


end


end #module SemanticEdgeFinder
