module GridSearch


using ...Types
using ...EdgeFinders
using ...Eval.Scores
using ..Utils
using ..InCore


export f1_grid_search, prec_grid_search, rec_grid_search
export prec_rec_grid_search


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

    @time res = InCore.process_single_chunk(chunk, seg, ef; params... )

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

    @time res = InCore.process_single_chunk(chunk, seg, ef; params... )

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

    @time res = InCore.process_single_chunk(chunk, seg, ef; params... )

    #NOTE: this will need to change if we change the
    # output format of ef's
    edges = collect(values(res))

    #NOTE: also output fmt dependent
    prec = Scores.prec_score(edges, gt_edges, false) #don't penalize dups for now
    rec  = Scores.rec_score(edges, gt_edges)

    precs[i]   = prec[1]
    recalls[i] = rec[1]
    gtcount[i] = length(rec[2])
    pcounts[i] = length(prec[2])
  end

  precs, recalls, pcounts, gtcount, range_names
end


end #module InCore
