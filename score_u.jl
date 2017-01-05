#!/usr/bin/env julia

__precompile__()

module score_u

export synapse_location_precision_recall
export edge_list_precision_recall

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
  #(TP, FP, FN)
end


"""

    compute_distance_matrix( centers1, centers2 )

  Computes a matrix of pairwise euclidean distances between two
  arrays of coordinate arrays
"""
function compute_distance_matrix( centers1, centers2 )

  distances = Array{Float64,Float64}( (length(centers1), length(centers2)) );

  for i in eachindex(centers1)
    for j in eachindex(centers2)
      distances[i,j] = norm(centers1[i] - centers2[j])
    end
  end

  distances

end


"""

    find_unmatched_ids( centers1, centers2, thresh )

  Finds the ids within both centers1 and centers2 which are not
  within thresh distance of a center in the other set.
"""
function find_unmatched_ids( centers1, centers2, thresh )

  ordered_keys1 = collect(keys(centers1))
  ordered_keys2 = collect(keys(centers2))

  distances = compute_distance_matrix(
    [ centers1[k] for k in ordered_keys1 ],
    [ centers2[k] for k in ordered_keys2 ] )

  min_distance1 = minimum(distances, 2)
  min_distance2 = minimum(distances, 1)

  unmatched1 = min_distance1 .>= thresh;
  unmatched2 = min_distance2 .>= thresh;

  ordered_keys1[unmatched1], ordered_keys2[unmatched2];
end


function synapse_location_precision_recall( proposed_centers, gt_centers, thresh )

  num_prop = length(proposed_centers)
  num_gt   = length(gt_centers)

  ordered_prop_centers = [ v for v in values(proposed_centers) ];
  ordered_gt_centers   = [ v for v in values(gt_centers) ];

  distances = compute_distance_matrix( ordered_prop_centers, ordered_gt_centers )

  min_distance_prop = minimum( distances, 2 )
  min_distance_gt   = minimum( distances, 1 )

  TPs_prop = sum( min_distance_prop .< thresh )
  TPs_gt   = sum( min_distance_gt   .< thresh )

  prec = TPs_prop / num_prop
  # This doesn't behave well if num_prop < num_gt
  # prec_conserv = TPs_gt   / num_prop

  recall = TPs_gt / num_gt

  return prec, recall
  #return TPs_prop, TPs_gt, num_prop, num_gt
end


end #module
