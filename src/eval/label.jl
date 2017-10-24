module Label

export label_errors

function label_errors{S,T}( pred_segs::AbstractArray{S,3},
                            gt_segs::AbstractArray{T,3}, fps::Dict, fns::Dict )

  labelled_volume = zeros(UInt32,size(pred_segs))

  for (i,(v1,v2)) in enumerate(zip(pred_segs, gt_segs))

    if v1 == 0 && v2==0   continue  end

    if     v1 != 0 && fps[v1]
      labelled_volume[i] = 2
    elseif v2 != 0 && fns[v2]
      labelled_volume[i] = 3
    elseif v1 != 0 #correct prediction
      labelled_volume[i] = 1
    end

  end

  labelled_volume
end


end #module Label
