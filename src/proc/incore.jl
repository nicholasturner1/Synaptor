module InCore


using ...Types
using ...EdgeFinders
using ...Eval.Scores
using ..Utils


export process_single_chunk


function process_single_chunk( chunk, seg, ef::EdgeFinder ; params...)

  params = Utils.collect_params(params)

  EdgeFinders.assign_aux_params!(ef, params)

  EdgeFinders.assign_aux_vols!(ef, chunk, seg, params[:volume_map])

  EdgeFinders.assign_ccs!(ef)

  EdgeFinders.findedges(ef)
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

    @time res = process_single_chunk(chunk, seg, ef; params... )

    edges = collect(values(res))

    scores[i] = score_fn( edges, gt_edges )[1]
  end

  scores, range_names
end


f1_grid_search(ch,seg,gt,ef; p...) = grid_search(ch,seg,gt,ef,Scores.f1score; p...)
f0p5_grid_search(ch,seg,gt,ef; p...) = grid_search(ch,seg,gt,ef,Scores.f0p5score; p...)


end #module InCore
