module OutOfCore

using ...Types
using ...Chunking
using ...SegUtils

using ..Utils
using ..InCore


function chunked_semantic_maps( seg::AbstractArray, weight::AbstractArray, classes,
                                chunk_shape )

  chunk_bboxes = Chunking.chunk_bounds(size(seg), chunk_shape)

  assignments = Array{Dict{Int,Int}}(size(chunk_bboxes)); 
  weights = Array{Dict{Int,Float64}}(size(chunk_bboxes));

  for (i,chunk) in enumerate(chunk_bboxes)

    seg_chunk = seg[chunk]
    w_chunk   = weight[chunk]

    a, w = SegUtils.make_semantic_assignment(seg_chunk, w_chunk, classes)

    assignments[i] = a
    weights[i] = w
  end

  assignments, weights
end


function chunked_edge_finding( net_output, seg, ef::EdgeFinder, chunk_shape; params... )

  params = Utils.collect_params(params)
  chunk_bboxes = Chunking.chunk_bounds(size(seg), chunk_shape)

  results = Array{Any}(size(chunk_bboxes))

  for (i,chunk) in enumerate(chunk_bboxes)

    output_chunk = net_output[chunk]
    seg_chunk    = seg[chunk]

    results[i] = InCore.process_chunk_w_continuations( output_chunk, seg, 
                                                       ef; params... )
  end

  results
end


end #module OutOfCore
