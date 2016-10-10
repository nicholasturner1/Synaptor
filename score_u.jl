#!/usr/bin/env julia
__precompile__()

#=
  Score Utils - score_u.jl
=#
module score_u 

export edge_list_precision_recall
export synapse_location_precision_recall


"""

    edge_list_precision_recall( predicted_list, ground_truth_list )

  Computes precision and recall over two arrays of tuples
"""
function edge_list_precision_recall( pred_list, gt_list )

  TP = length( Set(intersect(pred_list, gt_list)) )
  FP = length( setdiff(pred_list, gt_list)   )
  FN = length( setdiff(gt_list, pred_list)   )

  prec = TP / (TP + FP); recall = TP / (TP + FN )

  (prec, recall)
end


"""

    synapse_location_precision_recall( proposed_centers, gt_centers, thresh )

  Compares two lists of coordinate locations for
  synapses - one assumed to be ground-truth - and reports
  precision and recall scores for whether the locations
  exist within a threshold distance of one another
"""
function synapse_location_precision_recall( proposed_centers, gt_centers, thresh )

  num_prop = length(proposed_centers)
  num_gt   = length(gt_centers)

  distances = Array{Float64,Float64}( (num_prop, num_gt) )

  for j in 1:num_gt
    for i in 1:num_prop
      distances[i,j] = norm( (proposed_centers[i] - gt_centers[j]).^2 )
    end
  end

  min_distance_prop = minimum( distances, 2 )
  min_distance_gt   = minimum( distances, 1 )

  TPs_prop = sum( min_distance_prop .< thresh )
  TPs_gt   = sum( min_distance_gt   .< thresh )

  prec_liberal = TPs_prop / num_prop
  prec_conserv = TPs_gt   / num_prop

  recall = TPs_gt / num_gt

  return prec_conserv, recall
end



end#module
