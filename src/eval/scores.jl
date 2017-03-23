module Scores


export precision, recall, f1score, f0p5score, fscore
export false_positives, false_negatives


function precision( list1::Vector, list2::Vector, penalize_dups=true )

  list1 = penalize_dups? list1 : unique(list1)

  fps = false_positives(list1, list2)
  num_tps = sum(!fps)

  num_tps / length(list1), fps
end


function recall( list1::Vector, list2::Vector )

  fns = false_negatives(list1, list2)
  num_tps = sum(!fns)

  num_tps / length(list2), fns
end


function f1score( list1::Vector, list2::Vector, penalize_dups=true )
  fscore(list1, list2, 1, penalize_dups)
end


function f0p5score( list1::Vector, list2::Vector, panelize_dups=true )
  fscore(list1, list2, 0.5, penalize_dups)
end


function fscore( list1::Vector, list2::Vector, beta::Real, penalize_dups=true )

  list1 = penalize_dups? list1 : unique(list1)

  fps = false_positives(list1, list2)
  fns = false_negatives(list1, list2)

  num_fps, num_fns = sum(fps), sum(fns)
  num_tps = length(list2) - num_fns

  fscore( num_tps, num_fps, num_fns, beta ), fps, fns
end


function fscore( tp::Real, fp::Real, fn::Real, beta::Real )

  betasq = beta^2

  (1 + betasq) * tp / ((1 + betasq) * tp + betasq * fn + fp)
end


"""
Assumes that `edgelist2` represents the "ground truth"
"""
function false_positives( list1, list2 )

  gt_set = Set(list2)

  [ !(elem in gt_set) for elem in list1]
end

false_negatives(list1, list2) = false_positives(list2, list1)


end #module Scores
