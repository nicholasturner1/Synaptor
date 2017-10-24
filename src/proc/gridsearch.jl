module GridSearch


using ...Types
using ...EdgeFinders
using ...Eval
using ...Eval.Scores
using ...SegUtils
using ..Utils
using ..InCore


export ccs_at_params
export f1_grid_search, prec_grid_search, rec_grid_search
export prec_rec_grid_search, locs_grid_search, overlap_grid_search


function overlap_grid_search( psd_vol, gtsegs; params... )

  params = Utils.collect_params(params)

  param_grid, range_names = Utils.create_range_grid(params)

  num_gt = length(unique(gtsegs)) - 1 #1 for 0 segment
  ccs = Array{UInt32}(size(psd_vol));

  precs    = zeros(Float64, size(param_grid))
  recs     = zeros(Float64, size(param_grid))
  fscores  = zeros(Float64, size(param_grid))
  pcounts  = zeros(Int, size(param_grid))
  gtcount  = zeros(Int, size(param_grid))

  for i in eachindex(param_grid)

    grid_params = param_grid[i]
    for (k,v) in grid_params  params[k] = v  end

    print("Grid Params: ")
    for (k,v) in grid_params print("$k => $v ") end
    println("")
    tic()

    fill!(ccs,UInt32(0))
    ccs = SegUtils.dilated_components!(psd_vol, ccs, params[:dil_param],
                                             params[:CCthresh])
    SegUtils.filter_segs_by_size!(ccs, params[:SZthresh])
    num_preds = length(unique(ccs)) - 1 #1 for 0 segment

    if num_preds == 0
      precs[i]   = 1.0
      recs[i]    = 0.0
      fscores[i] = 0.0
      pcounts[i] = 0
      gtcount[i] = num_gt
      continue
    end

    prec, rec, fscore, _, _ = Eval.score_overlaps(ccs, gtsegs, params[:liberal])

    precs[i] = prec
    recs[i] = rec
    fscores[i] = fscore
    pcounts[i] = num_preds
    gtcount[i] = num_gt

    toc()
  end

  precs, recs, fscores, pcounts, gtcount, param_grid
end


function ccs_at_params( psd_vol; params... )

  params = Utils.collect_params(params)

  ccs = SegUtils.dilated_components(psd_vol, params[:dil_param],
                                    params[:CCthresh])
                                    
  SegUtils.filter_segs_by_size!(ccs, params[:SZthresh])

  ccs
end


function locs_grid_search( psd_vol, gtsegs; params... )

  params = Utils.collect_params(params)

  param_grid, range_names = Utils.create_range_grid(params)

  gtlocs = SegUtils.centers_of_mass(gtsegs)
  ccs = Array{UInt32}(size(psd_vol));

  precs    = zeros(Float64, size(param_grid))
  recs     = zeros(Float64, size(param_grid))
  fscores  = zeros(Float64, size(param_grid))
  pcounts  = zeros(Int, size(param_grid))
  gtcount  = zeros(Int, size(param_grid))

  for i in eachindex(param_grid)

    grid_params = param_grid[i]
    for (k,v) in grid_params  params[k] = v  end

    print("Grid Params: ")
    for (k,v) in grid_params print("$k => $v ") end
    println("")

    fill!(ccs,UInt32(0))
    @time ccs = SegUtils.connected_components3D!(psd_vol, ccs, params[:CCthresh])
    @time SegUtils.filter_segs_by_size!(ccs, params[:SZthresh])
    @time locs = SegUtils.centers_of_mass(ccs)
    println(length(unique(ccs)) - 1)
    println(length(locs))

    if length(locs) == 0
      precs[i]   = 1.0
      recs[i]    = 0.0
      fscores[i] = 0.0
      pcounts[i] = 0
      gtcount[i] = length(gtlocs)
      continue
    end

    prec, rec, fscore, _, _, _ = Eval.score_locs(locs, gtlocs,
                                                 params[:dist_thr],
                                                 params[:res])

    precs[i] = prec
    recs[i] = rec
    fscores[i] = fscore
    pcounts[i] = length(locs)
    gtcount[i] = length(gtlocs)
  end

  precs, recs, fscores, pcounts, gtcount, param_grid
end


function grid_search( chunk, seg, gt_edges, ef::EdgeFinder,
                      score_fn::Function; params... )

  params = Utils.collect_params(params)

  param_grid, range_names = Utils.create_range_grid(params)

  scores = zeros(Float64, size(param_grid))
  for i in eachindex(scores)

    #filling in params
    grid_params = param_grid[i]
    for (k,v) in grid_params params[k] = v end

    print("Grid Params: ")
    for (k,v) in grid_params print("$k => $v ") end
    println("")

    @time res = InCore.process_chunk(chunk, seg, ef; params... )

    #NOTE: this will need to change if we change the
    # output format of ef's
    edges = collect(values(res))

    scores[i] = score_fn( edges, gt_edges )[1]
  end

  scores, range_names
end


f1_grid_search(ch,seg,gt,ef; p...) = grid_search(ch,seg,gt,ef,Scores.f1score; p...)
f0p5_grid_search(ch,seg,gt,ef; p...) = grid_search(ch,seg,gt,ef,Scores.f0p5score; p...)


function grid_search_w_counts( chunk, seg, gt_edges, ef::EdgeFinder,
                               score_fn::Function; params... )

  params = Utils.collect_params(params)

  param_grid, range_names = Utils.create_range_grid(params)

  scores = zeros(Float64, size(param_grid))
  counts = zeros(Int, size(param_grid))
  for i in eachindex(scores)

    #filling in params
    grid_params = param_grid[i]
    for (k,v) in grid_params params[k] = v end

    print("Grid Params: ")
    for (k,v) in grid_params print("$k => $v ") end
    println("")

    @time res = InCore.process_chunk(chunk, seg, ef; params... )

    #NOTE: this will need to change if we change the
    # output format of ef's
    edges = collect(values(res))

    #NOTE: also output fmt dependent
    score_res = score_fn( edges, gt_edges )
    scores[i] = score_res[1]
    counts[i] = length(score_res[2])
  end

  scores, counts, range_names
end


#Associating the counts is useful for combining precision scores across dsets
prec_grid_search(ch,seg,gt,ef; p...) = grid_search_w_counts(ch,seg,gt,ef,Scores.prec_score; p...)
rec_grid_search(ch,seg,gt,ef; p...) = grid_search_w_counts(ch,seg,gt,ef,Scores.rec_score; p...)


function prec_rec_grid_search( chunk, seg, gt_edges, ef::EdgeFinder; params... )

  params = Utils.collect_params(params)

  param_grid, range_names = Utils.create_range_grid(params)

  precs   = zeros(Float64, size(param_grid))
  recalls = zeros(Float64, size(param_grid))
  pcounts = zeros(Int, size(param_grid))
  gtcount = zeros(Int, size(param_grid))

  for i in eachindex(param_grid)

    #filling in params
    grid_params = param_grid[i]
    for (k,v) in grid_params params[k] = v end

    print("Grid Params: ")
    for (k,v) in grid_params print("$k => $v ") end
    println("")

    @time res = InCore.process_chunk(chunk, seg, ef; params... )

    #NOTE: this will need to change if we change the
    # output format of ef's
    #edges = collect(values(res[1]))
    edges = EdgeFinders.filteredges(ef, res[1])
    edges = collect(values(edges))

    #NOTE: also output fmt dependent
    prec = Scores.prec_score(edges, gt_edges, false) #don't penalize dups for now
    rec  = Scores.rec_score(edges, gt_edges)

    precs[i]   = prec[1]
    recalls[i] = rec[1]
    println("Precision: $(precs[i]) Recall: $(recalls[i])")
    gtcount[i] = length(rec[2])
    pcounts[i] = length(prec[2])
  end

  precs, recalls, pcounts, gtcount, range_names
end


end #module InCore
