module Scores


export prec_score, rec_score, f1score, f0p5score, fscore
export false_positives, false_negatives


"""

    function prec_score( list1::Vector, list2::Vector, penalize_dups=true )

  Returns the precision score between two vectors of items, as well as
  a vector of bools indicating which items in `list1` were counted as false
  positives. The second list is assumed to be the "ground truth" version.

  If `penalize_dups` is false, will collapse `list1` to its unique values.
  The false positive vector can be interpreted by comparing to these unique
  values (i.e. call `unique(list1)` yourself, and compare).
"""
function prec_score( list1::Vector, list2::Vector, penalize_dups=true )

  list1 = penalize_dups? list1 : unique(list1)

  if length(list1) == 0 return (1,Bool[]) end

  fps = false_positives(list1, list2)
  num_tps = sum(!fps)

  num_tps / length(list1), fps
end

"""

    function rec_score( list1::Vector, list2::Vector )

  Returns the recall score between two vectors of items, as well as
  a vector of bools indicating which items in `list1` were counted as false
  negatives. The second list is assumed to be the "ground truth" version.
"""
function rec_score( list1::Vector, list2::Vector )

  if length(list2) == 0 return (1,Bool[]) end

  fns = false_negatives(list1, list2)
  num_tps = sum(!fns)

  num_tps / length(list2), fns
end


"""

    f1score( list1::Vector, list2::Vector, penalize_dups=true )

  Equivalent to fscore with `beta`=`1`.
"""
function f1score( list1::Vector, list2::Vector, penalize_dups=true )
  fscore(list1, list2, 1, penalize_dups)
end

"""

    f1score( list1::Vector, list2::Vector, penalize_dups=true )

  Equivalent to fscore with `beta`=`0.5`.
"""
function f0p5score( list1::Vector, list2::Vector, panelize_dups=true )
  fscore(list1, list2, 0.5, penalize_dups)
end

"""

    function fscore( list1::Vector, list2::Vector, beta::Real, penalize_dups=true )

  Returns the F-score between two vectors of items, as well as
  a two vectors of bools indicating which items in `list1` were counted as
  false positives & negatives. The second list is assumed to be the
  "ground truth" version.

  If `penalize_dups` is false, will collapse `list1` to its unique values.
  The false positive vector can be interpreted by comparing to these unique
  values (i.e. call `unique(list1)` yourself, and compare).
"""
function fscore( list1::Vector, list2::Vector, beta::Real, penalize_dups=true )

  list1 = penalize_dups? list1 : unique(list1)

  fps = false_positives(list1, list2)
  fns = false_negatives(list1, list2)

  num_fps, num_fns = sum(fps), sum(fns)
  num_tps = length(list2) - num_fns

  fscore( num_tps, num_fps, num_fns, beta ), fps, fns
end

"""

    function fscore( tp::Real, fp::Real, fn::Real, beta::Real )

  Computes the F-score from precomputed values for true positives, false
  positives, and false negatives.
"""
function fscore( tp::Real, fp::Real, fn::Real, beta::Real )

  betasq = beta^2

  (1 + betasq) * tp / ((1 + betasq) * tp + betasq * fn + fp)
end


function fscore( prec::Real, rec::Real, beta::Real )

  betasq = beta^2

  (1 + betasq) / ( 1/prec + betasq/rec )
end


"""

    false_positives( list1, list2 )

  Finds the false positives within `list1`

  Assumes that `list2` represents the "ground truth"
"""
function false_positives( list1, list2, gt_dups=false )

  gt_counts = Dict{eltype(list2),Int}()
  for v in list2
    if !haskey(gt_counts,v)  gt_counts[v] = 1
    else                     gt_counts[v] += 1
    end
  end

  fps = zeros(Bool,length(list1))

  for (i,v) in enumerate(list1)

    if haskey(gt_counts,v) && gt_counts[v] > 0
      gt_counts[v] -= 1
    else
      fps[i] = true
    end

  end

  fps
end


"""

    false_negatives( list1, list2 )

  Finds the false positives within `list1`

  Assumes that `list2` represents the "ground truth" and has no duplicates
"""
false_negatives(list1, list2) = false_positives(list2, list1)


end #module Scores
