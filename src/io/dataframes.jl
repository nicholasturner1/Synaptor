module DataFramesIO

using DataFrames
using Feather


export read_edge_file, write_edge_file
export read_semmap, write_semmap
export read_idmap, write_idmap
export read_column, write_column
export read_assignments


function read_idmap(input_fname)

  @assert isfile(input_fname)
  local df
  try
    df = DataFrames.readtable(input_fname)
  catch
    return Dict{Int,Int}()
  end

  colnames = names(DataFrames.index(df))
  @assert :ids in colnames  "No id column"

  idmap = read_df_columns(df, "mapped_val")

  idmap
end


function write_idmap(idmap, output_fname)

  ids = collect(keys(idmap))

  cols = Any[ids]; colnames = Symbol[:ids]

  m_cols, m_names = make_df_columns(ids, idmap, "mapped_val")
  append!(cols, m_cols); append!(colnames, m_names)

  DataFrames.writetable(output_fname, DataFrame(cols, colnames))
end

function write_column(col, output_fname)

  cols = Any[col]; colnames = Symbol[:ids]

  DataFrames.writetable(output_fname, DataFrame(cols, colnames))
end

function read_column(input_fname)

  @assert isfile(input_fname)
  local df
  try
    df = DataFrames.readtable(input_fname)
  catch
    return Int[]
  end

  colnames = names(DataFrames.index(df))
  @assert :ids in colnames "No id column"

  Array(df[:ids])
end


function read_edge_file(input_fname)

  @assert isfile(input_fname)
  local df
  try
    df = DataFrames.readtable(input_fname)
  catch
    return Dict{Int,Tuple{Int,Int}}(), Dict{Int,Vector{Int}}(), Dict{Int,Int}(), Dict{Int,Vector{Int}}()
  end

  colnames = names(DataFrames.index(df))
  @assert :ids in colnames  "No id column"

  segs = read_df_columns(df, "segs")
  locs = read_df_columns(df, "locs")
  sizes = read_df_columns(df, "sizes")
  bboxes = read_df_columns(df, "bboxes")

  #just to be sure that the other code is compatible...
  segs = Dict( k => (v...) for (k,v) in segs )

  segs, locs, sizes, bboxes
end


function write_edge_file(segs, locs, sizes, bboxes, output_fname)

  ids = collect(keys(segs))

  cols = Any[ids]; colnames = Symbol[:ids]

  s_cols, s_names = make_df_columns(ids, segs, "segs")
  append!(cols, s_cols); append!(colnames, s_names)

  l_cols, l_names = make_df_columns(ids, locs, "locs")
  append!(cols, l_cols); append!(colnames, l_names)

  sz_cols, sz_names = make_df_columns(ids, sizes, "sizes")
  append!(cols, sz_cols); append!(colnames, sz_names)

  bb_cols, bb_names = make_df_columns(ids, bboxes, "bboxes")
  append!(cols, bb_cols); append!(colnames, bb_names)

  #DataFrame(cols, colnames)
  DataFrames.writetable(output_fname, DataFrame(cols, colnames))
end

function write_edge_file(segs, locs, output_fname)

  ids = collect(keys(segs))

  cols = Any[ids]; colnames = Symbol[:ids]

  s_cols, s_names = make_df_columns(ids, segs, "segs")
  append!(cols, s_cols); append!(colnames, s_names)

  l_cols, l_names = make_df_columns(ids, locs, "locs")
  append!(cols, l_cols); append!(colnames, l_names)

  #DataFrame(cols,colnames)
  DataFrames.writetable(output_fname, DataFrame(cols, colnames))
end


function write_semmap(assignments, weights, output_fname)

  ids = collect(keys(assignments))

  cols = Any[ids]; colnames = Symbol[:ids]

  a_cols, a_colnames = make_df_columns(ids, assignments, "assignments")
  append!(cols, a_cols); append!(colnames, a_colnames)

  w_cols, w_colnames = make_df_columns(ids, weights,     "weights")
  append!(cols, w_cols); append!(colnames, w_colnames)

  #DataFrame(cols, colnames)
  DataFrames.writetable(output_fname, DataFrame(cols, colnames))
end


function read_semmap(input_fname)

  @assert isfile(input_fname)
  local df
  try
    df = DataFrames.readtable(input_fname)
  catch
    return Dict{Int,Int}(), Dict{Int,Vector{Float32}}()
  end

  assignments = read_df_columns(df, "assignments")
  weights     = read_df_columns(df, "weights")

  assignments, weights
end


function read_assignments(input_fname)
  
  @assert isfile(input_fname)
  local df
  try
    df = DataFrames.readtable(input_fname)
  catch
    return Dict{Int,Int}()
  end

  read_df_columns(df, "assignments")
end

# make_base_df(ids) = DataFrame(Any[ids], [:ids])

function make_df_columns(keys, vals, basename)

  @assert length(keys) <= length(vals)

  if length(keys) == 0  return (Any[Int[]],[Symbol(basename)])  end

  first_val = first(values(vals))

  if length(first_val) == 1
    col = [ vals[k] for k in keys ]
    return (Any[col],[Symbol(basename)])
  end

  cols = Any[]; colnames = Symbol[];
  for i in 1:length(first_val)
    col = [ vals[k][i] for k in keys ]
    colname = Symbol("$(basename)_$i")

    push!(cols, col); push!(colnames, colname)
  end

  cols, colnames
end


function read_df_columns(df, basename)

  colnames = names(DataFrames.index(df))
  num_cols = 0


  if Symbol(basename) in colnames
    return Dict( k => v for (k,v) in zip(Array(df[:ids]),Array(df[Symbol(basename)])) )
  end


  relevant_names = []; i = 1
  while Symbol("$(basename)_$i") in colnames
    push!(relevant_names, Symbol("$(basename)_$i"))
    i += 1
  end

  if length(relevant_names) == 0  return Dict()  end


  ids = Array(df[:ids])
  cols = [Array(df[n]) for n in relevant_names]

  res = Dict{Int,Vector{eltype(cols[1])}}();

  for (i,v) in enumerate(zip(cols...))
    res[ids[i]] = collect(v)
  end

  res
end


end #module FeatherIO
