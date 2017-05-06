module WorkerTasks

using Synaptor; S = Synaptor;
using Synaptor.Consolidation.Continuations
using S3Dicts, BigArrays
using HDF5


#S3 organization
semmap_subdir      = "semmaps"
nh_semmap_subdir   = "nh_semmaps"
ch_edge_subdir     = "ch_edges"
ch_cont_subdir     = "ch_continuations"
ch_contedge_subdir = "ch_cont_edges"
cont_merge_subdir  = "cont_mergers"
id_map_subdir      = "idmaps"
cont_idmap_subdir  = "cont_idmaps"


ef_params = Dict(
  :volume_map => Dict( :PSDvol => 4 ),
  :CCthresh => 0.2, :SZthresh => 700,
  :dilation => 5, :axon_label => 1,
  :dend_label => 2 )


export semantic_map, expand_semmaps, find_edges
export consolidateids, conscontinuations, consolidatedups
export relabel_seg, convert_semmap, full_find_edges


#==========================
JOB1: Semantic Mapping
==========================#

function semantic_map(taskdict, classes=[1,2,3])

  #Extracting task args
  chunk_start   = taskdict["start"]
  chunk_end     = taskdict["end"]
  chx, chy, chz = taskdict["chunk_i"]
  seg_s3_path   = taskdict["seg_path"]
  sem_s3_path   = taskdict["sem_path"]
  base_s3_path  = taskdict["base_outpath"]

  seg_BA = BigArray(S3Dict( seg_s3_path ))
  sem_BA = BigArray(S3Dict( sem_s3_path ))


  #Downloading data
  chunk_bbox = S.BBox(chunk_start, chunk_end)
  seg_chunk = seg_BA[chunk_bbox]
  sem_chunk = sem_BA[chunk_bbox,1:3]

  mst_rl_fname = "remap_mean_base1.h5"
  s3_mst_rl_fname = joinpath(base_s3_path,mst_rl_fname)
  download_mst_rl(s3_mst_rl_fname, mst_rl_fname)
  mst_rl = h5read(mst_rl_fname,"main");

  @time S.relabel_data!(seg_chunk, mst_rl)

  #Performing mapping
  @time a, w = S.make_semantic_assignment(seg_chunk, sem_chunk, classes)


  #Writing results to s3
  output_fname = "chunk_$(chx)_$(chy)_$(chz)_semmap.fth"
  s3_output_fname = joinpath(base_s3_path,semmap_subdir,output_fname)
  S.InputOutput.write_semmap(a,w,output_fname)
  run( `aws s3 mv $output_fname $s3_output_fname`)

end


function download_mst_rl(s3_fname, local_fname)
  if !isfile(local_fname)
    run( `aws s3 cp $s3_fname $local_fname` )
  end
end

#==========================
JOB2: Semantic Map Expansion
==========================#

function expand_semmaps(taskdict)

  #Extracting task args
  chx, chy, chz = taskdict["chunk_i"]
  base_s3_path  = taskdict["base_outpath"]
  sx,sy,sz    = taskdict["max_chunk_i"]


  #Downloading data
  s3_semmap_dir = joinpath(base_s3_path,semmap_subdir)
  rel_indices = relevant_indices(chx,chy,chz,sx,sy,sz)
  @time download_relevant_semmaps(rel_indices, s3_semmap_dir)
  @time w_arr = load_relevant_weights(rel_indices)

  @time nh_weight = S.SegUtils.SemanticMap.addsemweights( w_arr... )
  # @time nh_weights = S.neighborhood_semmaps(semmap_arr, 0)
  @time nh_assigns = S.make_assignment(nh_weight)

  #Writing results to s3
  output_fname = "chunk_$(chx)_$(chy)_$(chz)_nh_semmap.fth"
  S.InputOutput.write_semmap(nh_assigns, nh_weight, output_fname)
  s3_output_fname = joinpath(base_s3_path, nh_semmap_subdir,output_fname)
  run( `aws s3 cp $output_fname $s3_output_fname` )

end


function load_all_semmaps(sx,sy,sz)

  semmap_arr = Array{Dict{Int,Vector{Float64}}}(sx,sy,sz)

  for z in 1:sz, y in 1:sy, x in 1:sx

    println((x,y,z))
    @time a,w = S.InputOutput.read_semmap("chunk_$(x)_$(y)_$(z)_semmap.fth")

    semmap_arr[x,y,z] = w
  end

  semmap_arr
end


function save_all_semmaps(assigns,weights,output_dir)

  if !isdir(output_dir)  mkdir(output_dir)  end

  @assert size(assigns) == size(weights)
  sx,sy,sz = size(assigns)

  for z in 1:sz, y in 1:sy, x in 1:sx
    a,w = assigns[x,y,z], weights[x,y,z]

    output_fname = joinpath(output_dir,"chunk_$(x)_$(y)_$(z)_nhsemmap.fth")
    S.InputOutput.write_semmap(a,w,output_fname)
  end

end


#==========================
JOB3: Chunk Edge Finding
==========================#


function find_edges(taskdict)

  #Extracting task args
  chunk_start   = taskdict["start"]
  chunk_end     = taskdict["end"]
  chx, chy, chz = taskdict["chunk_i"]
  psdseg_path   = taskdict["psdseg_path"]
  seg_s3_path   = taskdict["seg_path"]
  sem_s3_path   = taskdict["sem_path"]
  base_s3_path  = taskdict["base_outpath"]

  seg_BA = BigArray(S3Dict( seg_s3_path ))
  sem_BA = BigArray(S3Dict( sem_s3_path ))


  #Downloading data
  nh_semmap_fname = joinpath(base_s3_path,nh_semmap_subdir,
                             "chunk_$(chx)_$(chy)_$(chz)_nh_semmap.fth")
  run( `aws s3 cp $nh_semmap_fname nh_semmap.fth` )
  nh_semmap, weights = S.InputOutput.read_semmap("nh_semmap.fth")
  chunk_bbox = S.BBox(chunk_start, chunk_end)
  seg_ch = seg_BA[chunk_bbox]
  S.dilate_by_k!(seg_ch,7)
  sem_ch = sem_BA[chunk_bbox,1:4]

  mst_rl_fname = "remap_mean_base1.h5"
  s3_mst_rl_fname = joinpath(base_s3_path, mst_rl_fname)
  download_mst_rl(s3_mst_rl_fname, mst_rl_fname)
  mst_rl = h5read(mst_rl_fname,"main");


  @time S.relabel_data!(seg_ch,mst_rl);

  offset = chunk_start - 1;
  ef = S.SemanticEdgeFinder();
  psdseg_BA = BigArray( S3Dict(psdseg_path) );


  @time (edges, locs, sizes, bboxes, ccs, conts
  ) = S.process_chunk_w_continuations(sem_ch, seg_ch, ef;
                                      offset=offset,
                                      semmap=nh_semmap,
                                      ef_params... )

  #Writing results to s3
  edge_output_fname = "chunk_$(chx)_$(chy)_$(chz)_ch_edges.fth"
  s3_edge_output_fname = joinpath(base_s3_path,ch_edge_subdir,edge_output_fname)
  S.InputOutput.write_edge_file(edges, locs, sizes, bboxes, edge_output_fname)
  run( `aws s3 cp $edge_output_fname $s3_edge_output_fname` )

  psdseg_BA[chunk_bbox] = round(eltype(psdseg_BA),ccs)

  cont_output_fname = "chunk_$(chx)_$(chy)_$(chz)_ch_conts.h5"
  s3_cont_output_fname = joinpath(base_s3_path,ch_edge_subdir,cont_output_fname)
  S.InputOutput.write_continuations(cont_output_fname, conts)
  run( `aws s3 cp $cont_output_fname $s3_cont_output_fname` )

end


#==========================
JOB4: Whole Seg ID Consolidation
==========================#

function consolidateids(taskdict)

  #Extracting task args
  sx,sy,sz    = taskdict["max_chunk_i"]
  base_s3_path  = taskdict["base_outpath"]


  #Downloading data
  s3_semmap_dir = joinpath(base_s3_path,ch_edge_subdir)
  run( `aws s3 cp --recursive $s3_semmap_dir . --exclude "*.h5"` )
  @time edge_arr, locs_arr, sizes_arr, bboxes_arr = load_all_edges(sx,sy,sz)


  @time id_maps = S.consolidate_ids( map( x -> Set(keys(x)), edge_arr) )
  edges  = S.apply_id_maps(edge_arr, id_maps)
  locs   = S.apply_id_maps(locs_arr, id_maps)
  sizes  = S.apply_id_maps(sizes_arr, id_maps)
  bboxes = S.apply_id_maps(bboxes_arr, id_maps)


  #Adding types to results
  edges  = Dict{Int,Tuple{Int,Int}}(k=>v for (k,v) in edges)
  locs   = Dict{Int,Vector{Int}}(k=>v for (k,v) in locs)
  sizes  = Dict{Int,Int}(k=>v for (k,v) in sizes)
  bboxes = Dict{Int,Vector{Int}}(k=>v for (k,v) in bboxes);


  #Writing results to s3
  edge_output_fname = "consolidated_edges_wo_conts.fth"
  s3_edge_output_fname = joinpath(base_s3_path,edge_output_fname)
  S.InputOutput.write_edge_file(edges, locs, sizes, bboxes, edge_output_fname)
  run( `aws s3 cp $edge_output_fname $s3_edge_output_fname` )

  save_all_idmaps(id_maps, id_map_subdir)
  s3_output_fname = joinpath(base_s3_path,id_map_subdir)
  run( `aws s3 cp --recursive $id_map_subdir $s3_output_fname` )

  local next_id
  try
    next_id = maximum(keys(edges)) + 1
  catch
    next_id = 1
  end

  next_id_s3_fname = joinpath(base_s3_path,"next_id")
  write_next_id(next_id)
  run( `aws s3 cp next_id $next_id_s3_fname` )

end

function write_next_id(next_id)

  open("next_id","w") do f
    write(f,"$next_id")
  end

end

function load_all_edges(sx,sy,sz)

  edge_arr  = Array{Dict}(sx,sy,sz)
  locs_arr  = Array{Dict}(sx,sy,sz)
  sizes_arr = Array{Dict}(sx,sy,sz)
  bboxes_arr = Array{Dict}(sx,sy,sz)

  for z in 1:sz, y in 1:sy, x in 1:sx

    println((x,y,z))
    ch_edge_fname = "chunk_$(x)_$(y)_$(z)_ch_edges.fth"
    @time ed,l,s,b = S.InputOutput.read_edge_file(ch_edge_fname)

    edge_arr[x,y,z] = ed
    locs_arr[x,y,z] = l
    sizes_arr[x,y,z] = s
    bboxes_arr[x,y,z] = b
  end

  edge_arr, locs_arr, sizes_arr, bboxes_arr
end


function save_all_idmaps(id_maps, subdir_name)

  if !isdir(subdir_name)  mkdir(subdir_name)  end

  sx,sy,sz = size(id_maps)

  for z in 1:sz, y in 1:sy, x in 1:sx
    map = id_maps[x,y,z]

    output_fname = joinpath(subdir_name,"chunk_$(x)_$(y)_$(z)_idmap.fth")
    S.InputOutput.write_idmap(map,output_fname)
  end

end


#==========================
JOB5: Continuation Consolidation
==========================#

function conscontinuations(taskdict)

  #Extracting task args
  sx,sy,sz    = taskdict["max_chunk_i"]
  total_vol   = S.BBox(taskdict["total_vol"]...)
  chunk_shape = taskdict["chunk_shape"]
  offset      = taskdict["offset"]
  boundtype   = taskdict["boundtype"]
  base_s3_path  = taskdict["base_outpath"]


  #Downloading data
  s3_ch_cont_dir = joinpath(base_s3_path,ch_cont_subdir)
  run( `aws s3 cp --recursive $s3_ch_cont_dir .` )
  #full_semmap_fname = "full_semmap.fth"
  #s3_semmap_fname = joinpath(base_s3_path,full_semmap_fname)
  #run( `aws s3 cp $s3_semmap_fname .` )
  s3_nh_semmap_dir = joinpath(base_s3_path, nh_semmap_subdir)
  run( `aws s3 cp --recursive $s3_nh_semmap_dir .` )
  next_id_fname = joinpath(base_s3_path,"next_id")
  run( `aws s3 cp $next_id_fname .` )

  cont_arr = load_all_continuations(sx,sy,sz)
  #semmap, weights = S.InputOutput.read_semmap(full_semmap_fname)
  semmap_arr = load_all_nh_semmaps(sx,sy,sz)
  next_id = load_next_id()
  size_thr = ef_params[:SZthresh]


  (edges, locs, sizes, bboxes, idmaps
  #) = S.consolidate_continuations(cont_arr, semmap, size_thr, next_id)
  ) = S.consolidate_continuations(cont_arr, semmap_arr, size_thr, next_id)

  #Writing results to s3
  edge_output_fname = "continuation_edges.fth"
  s3_edge_output_fname = joinpath(base_s3_path,edge_output_fname)
  S.InputOutput.write_edge_file(edges, locs, sizes, bboxes, edge_output_fname)
  run( `aws s3 cp $edge_output_fname $s3_edge_output_fname` )

  save_all_idmaps(idmaps, cont_idmap_subdir)
  s3_output_fname = joinpath(base_s3_path,cont_idmap_subdir)
  run( `aws s3 cp --recursive $cont_idmap_subdir $s3_output_fname` )
end


function load_all_continuations(sx,sy,sz)

  cont_arr = Array{Vector{Continuation}}(sx,sy,sz)

  for z in 1:sz, y in 1:sy, x in 1:sx

    println((x,y,z))
    @time cs = S.InputOutput.read_continuations("chunk_$(x)_$(y)_$(z)_ch_conts.h5")

    cont_arr[x,y,z] = cs
  end

  cont_arr
end

function load_all_nh_semmaps(sx,sy,sz)

  semmap_arr = Array{Dict{Int,Int}}(sx,sy,sz)

  for z in 1:sz, y in 1:sy, x in 1:sx

    println((x,y,z))
    @time a,w = S.InputOutput.read_semmap("chunk_$(x)_$(y)_$(z)_nh_semmap.fth")

    semmap_arr[x,y,z] = a
  end

  semmap_arr
end

function load_next_id()
  parse(Int,String(read("next_id")))
end

#==========================
JOB6: Consolidating Likely Duplicates
==========================#

function consolidatedups(taskdict, dist_thr=1000, res=[3.85,3.85,40])

  #Extracting task args
  base_s3_path  = taskdict["base_outpath"]

  #Downloading data
  whole_edge_fname = "consolidated_edges_wo_conts.fth"
  s3_edges_wo_continuations = joinpath(base_s3_path,whole_edge_fname)
  run( `aws s3 cp $s3_edges_wo_continuations .` )

  cont_edge_fname = "continuation_edges.fth"
  s3_continuation_edge_fname = joinpath(base_s3_path,cont_edge_fname)
  run( `aws s3 cp $s3_continuation_edge_fname .`)

  edges, locs, sizes, bboxes = S.InputOutput.read_edge_file(whole_edge_fname)
  ec, lc, sc, bc = S.InputOutput.read_edge_file(cont_edge_fname)

  merge!(edges, ec)
  merge!(locs, lc)
  merge!(sizes, sc)
  merge!(bboxes, bc)

  @time new_es, new_ls, new_ss, new_bs, idmap = S.consolidate_dups(edges, locs, sizes,
                                                                   bboxes, dist_thr, res)

  #Writing results to s3
  final_edge_fname = "final_edges.fth"
  S.InputOutput.write_edge_file(new_es, new_ls, new_ss, new_bs, final_edge_fname)
  s3_final_edge_fname = joinpath(base_s3_path, final_edge_fname)
  run( `aws s3 cp $final_edge_fname $s3_final_edge_fname` )

  dedup_idmap_fname = "dedup_idmap.fth"
  S.InputOutput.write_idmap(idmap, dedup_idmap_fname)
  s3_dedup_idmap_fname = joinpath(base_s3_path, dedup_idmap_fname)
  run( `aws s3 cp $dedup_idmap_fname $s3_dedup_idmap_fname` )

end

#==========================
JOB7: Segment Relabelling
==========================#


function relabel_seg(taskdict)

  #Extracting task args
  chunk_start   = taskdict["start"]
  chunk_end     = taskdict["end"]
  chx, chy, chz = taskdict["chunk_i"]
  psdseg_path   = taskdict["psdseg_path"]
  base_s3_path  = taskdict["base_outpath"]

  #Downloading data
  whole_seg_idmap_path = joinpath(base_s3_path,id_map_subdir,
                                  "chunk_$(chx)_$(chy)_$(chz)_idmap.fth")
  run( `aws s3 cp $whole_seg_idmap_path whole_seg_idmap.fth` )

  cont_idmap_path = joinpath(base_s3_path,cont_idmap_subdir,
                            "chunk_$(chx)_$(chy)_$(chz)_idmap.fth")
  run( `aws s3 cp $cont_idmap_path continuation_idmap.fth` )

  dedup_idmap_fname = "dedup_idmap.fth"
  s3_dedup_idmap_fname = joinpath(base_s3_path, dedup_idmap_fname)
  run( `aws s3 cp $s3_dedup_idmap_fname $dedup_idmap_fname`)


  whole_idmap = S.InputOutput.read_idmap("whole_seg_idmap.fth")
  cont_idmap = S.InputOutput.read_idmap("continuation_idmap.fth")
  dedup_idmap = S.InputOutput.read_idmap(dedup_idmap_fname)

  psdseg_BA = BigArray( S3Dict(psdseg_path) );

  chunk_bbox = S.BBox(chunk_start, chunk_end)
  psdseg_chunk = psdseg_BA[chunk_bbox]


  @time S.relabel_data!(psdseg_chunk, cont_idmap)
  @time S.relabel_data!(psdseg_chunk, whole_idmap)
  @time S.relabel_data!(psdseg_chunk, dedup_idmap)

  #Writing results to s3
  psdseg_BA[chunk_bbox] = psdseg_chunk
end

#==========================
JOB8: Semantic Map Conversion
==========================#


function convert_semmap(taskdict)

  #Extracting task args
  chx, chy, chz = taskdict["chunk_i"]
  base_s3_path  = taskdict["base_outpath"]

  #Downloading data
  s3_semmap_dir = joinpath(base_s3_path,semmap_subdir)
  target_semmap_fname = "chunk_$(chx)_$(chy)_$(chz)_semmap.csv"
  run( `aws s3 cp $s3_semmap_dir/$target_semmap_fname $target_semmap_fname` )

  a, w = S.InputOutput.BasicIO.read_semmap( target_semmap_fname, 2 )


  #Writing results to s3
  output_semmap_fname = "chunk_$(chx)_$(chy)_$(chz)_semmap.fth"
  S.InputOutput.FeatherIO.write_semmap(a,w,output_semmap_fname)
  run( `aws s3 cp $output_semmap_fname $s3_semmap_dir/$output_semmap_fname` )
end

#==========================
JOB9: EF + Semantic Map
==========================#


function full_find_edges(taskdict)

  #Extracting task args
  chunk_start   = taskdict["start"]
  chunk_end     = taskdict["end"]
  chx, chy, chz = taskdict["chunk_i"]
  psdseg_path   = taskdict["psdseg_path"]
  seg_s3_path   = taskdict["seg_path"]
  sem_s3_path   = taskdict["sem_path"]
  base_s3_path  = taskdict["base_outpath"]

  seg_BA = BigArray(S3Dict( seg_s3_path ))
  sem_BA = BigArray(S3Dict( sem_s3_path ))


  #Downloading data
  chunk_bbox = S.BBox(chunk_start, chunk_end)
  seg_ch = seg_BA[chunk_bbox]
  S.dilate_by_k!(seg_ch,7)
  sem_ch = sem_BA[chunk_bbox,1:4]
  psdseg_BA = BigArray( S3Dict(psdseg_path) );

  @time a,w = S.make_semantic_assignment(seg_ch, sem_ch, [1,2,3])

  offset = chunk_start - 1;
  ef = S.SemanticEdgeFinder();


  @time (edges, locs, sizes, bboxes, ccs, conts
  ) = S.process_chunk_w_continuations(sem_ch, seg_ch, ef;
                                      offset=offset,
                                      semmap=nh_semmap,
                                      ef_params... )

  #Writing results to s3
  edge_output_fname = "chunk_$(chx)_$(chy)_$(chz)_ch_edges.fth"
  s3_edge_output_fname = joinpath(base_s3_path,ch_edge_subdir,edge_output_fname)
  S.InputOutput.write_edge_file(edges, locs, sizes, bboxes, edge_output_fname)
  run( `aws s3 cp $edge_output_fname $s3_edge_output_fname` )

  psdseg_BA[chunk_bbox] = round(eltype(psdseg_BA),ccs)

  cont_output_fname = "chunk_$(chx)_$(chy)_$(chz)_ch_conts.h5"
  s3_cont_output_fname = joinpath(base_s3_path,ch_cont_subdir,cont_output_fname)
  S.InputOutput.write_continuations(cont_output_fname, conts)
  run( `aws s3 cp $cont_output_fname $s3_cont_output_fname` )

end

#==========================
JOB10: Find continuation edges
==========================#


function find_cont_edges(taskdict)

  #Extracting task args
  chx, chy, chz = taskdict["chunk_i"]
  base_s3_path  = taskdict["base_outpath"]
  sx,sy,sz    = taskdict["max_chunk_i"]


  #Downloading data
  rel_indices = relevant_indices(chx,chy,chz,sx,sy,sz)
  s3_dir = joinpath(base_s3_path,ch_cont_subdir)
  @time download_relevant_continuation_files(rel_indices, s3_dir)
  @time c_arr = load_relevant_continuation_files(rel_indices)

  @time cont_edges = S.Consolidation.find_continuation_edges(c_arr,2,2,2)
  edge_segids = Dict{Int,Tuple{Int,Int}}( i => (edge[1],edge[2][1])
                                          for (i,edge) in enumerate(cont_edges) )
  edge_chlocs = Dict{Int,Vector{Int}}( i => edge[2][2]
                                          for (i,edge) in enumerate(cont_edges) )

  chunk_cont_segids = collect(Set([ c.segid for c in c_arr[2,2,2] ]))
  #making sure the result is typed
  if length(chunk_cont_segids) == 0  chunk_cont_segids = Int[]  end

  #Writing results to s3
  edge_output_fname = "chunk_$(chx)_$(chy)_$(chz)_cont_edges.fth"
  s3_edge_output_fname = joinpath(base_s3_path,ch_contedge_subdir,edge_output_fname)
  @time S.InputOutput.write_edge_file(edge_segids, edge_chlocs, edge_output_fname) #notimp
  run( `aws s3 cp $edge_output_fname $s3_edge_output_fname` )

  segid_output_fname = "chunk_$(chx)_$(chy)_$(chz)_cont_segids.fth"
  s3_segid_output_fname = joinpath(base_s3_path,ch_contedge_subdir,segid_output_fname)
  @time S.InputOutput.write_column(chunk_cont_segids, segid_output_fname)
  run( `aws s3 cp $segid_output_fname $s3_segid_output_fname`)

end

function relevant_indices(chx,chy,chz,sx,sy,sz)

  rel_indices = Array{Tuple{Int,Int,Int},3}(3,3,3)
  rel_indices[:] = (-1,-1,-1)

  for z in 1:3, y in 1:3, x in 1:3

    new_i = (chx + x-2, chy + y-2, chz + z-2)
    if outofbounds(new_i,sx,sy,sz)  continue  end
    rel_indices[x,y,z] = new_i
  end

  rel_indices
end

@inline function outofbounds(new_i,sx,sy,sz)
  new_i[1] > sx || new_i[1] < 1 ||
  new_i[2] > sy || new_i[2] < 1 ||
  new_i[3] > sz || new_i[3] < 1
end

function download_relevant_continuation_files(rel_indices, s3_dir_path)

  chx, chy, chz = rel_indices[2,2,2]

  for i in rel_indices
    if i == (-1,-1,-1)  continue  end

    x,y,z = i
    continuations_fname = "chunk_$(x)_$(y)_$(z)_ch_conts.h5"

    if !isfile(continuations_fname)
      s3_fname = joinpath(s3_dir_path, continuations_fname)
      run( `aws s3 cp $s3_fname $continuations_fname` )
    end
  end

end

function load_relevant_continuation_files(rel_indices)

  sx,sy,sz = size(rel_indices)
  c_arr = Array{Vector{Continuation}}((sx,sy,sz))

  for z in 1:sz, y in 1:sy, x in 1:sx

    if rel_indices[x,y,z] == (-1,-1,-1)  c_arr[x,y,z] = Continuation[]  end

    println((x,y,z))
    lx,ly,lz = rel_indices[x,y,z]
    println((lx,ly,lz))
    fname = "chunk_$(lx)_$(ly)_$(lz)_ch_conts.h5"
    @time cs = S.InputOutput.read_continuations(fname)

    c_arr[x,y,z] = cs

  end

  c_arr
end

#==========================
JOB11: Merge continuation graph
==========================#

function merge_cont_edges(taskdict)

  #Extracting task args
  base_s3_path  = taskdict["base_outpath"]
  sx,sy,sz    = taskdict["max_chunk_i"]
  chx,chy,chz = taskdict["chunk_i"]


  #Downloading data
  s3dir = joinpath(base_s3_path,ch_contedge_subdir)
  run( `aws s3 cp --recursive $s3dir .` )
  next_id_fname = joinpath(base_s3_path,"next_id")
  run( `aws s3 cp $next_id_fname .`)
  next_id = load_next_id()


  edges_arr = load_all_cont_edges(sx,sy,sz) #notimp
  segids_arr = load_all_segids(sx,sy,sz) #notimp
  mergers_arr = Consolidation.merge_cont_edges(edges_arr, segids_arr) #notimp

  write_all_mergers(mergers_arr)
  #Writing results to s3
  edge_output_fname = "chunk_$(chx)_$(chy)_$(chz)_cont_edges.fth"
  s3_edge_output_fname = joinpath(base_s3_path,ch_contedge_subdir,edge_output_fname)
  S.InputOutput.write_edge_file(edges, locs, edge_output_fname)
  run( `aws s3 cp $edge_output_fname $s3_edge_output_fname` )
end

#==========================
JOB12: Global semantic map
==========================#


function global_semmap(taskdict)

  #Extracting task args
  base_s3_path = taskdict["base_outpath"]
  sx,sy,sz     = taskdict["max_chunk_i"]

  #Downloading data
  s3dir = joinpath(base_s3_path, semmap_subdir)
  @time run( `aws s3 cp --recursive $s3dir .` )

  @time semmap_arr = load_all_semmaps(sx,sy,sz)

  @time full_semmap = S.SegUtils.SemanticMap.addsemweights( semmap_arr... )
  @time assignments = S.SegUtils.SemanticMap.make_assignment( full_semmap )

  output_fname = "full_semmap.fth"
  s3_output_fname = joinpath(base_s3_path,output_fname)
  S.InputOutput.write_semmap(assignments, full_semmap, output_fname)
  run( `aws s3 cp $output_fname $s3_output_fname` )

end


function load_all_semweights(sx,sy,sz)

  semmap_arr = Array{Dict{Int,Vector{Float64}}}(sx,sy,sz)

  for z in 1:sz, y in 1:sy, x in 1:sx

    println((x,y,z))
    @time a,w = S.InputOutput.read_semmap("chunk_$(x)_$(y)_$(z)_semmap.fth")

    semmap_arr[x,y,z] = w
  end

  semmap_arr
end

function download_relevant_semmaps(rel_indices, s3_dir_path)

  chx, chy, chz = rel_indices[2,2,2]

  for i in rel_indices
    if i == (-1,-1,-1)  continue  end

    x,y,z = i
    local_fname = "chunk_$(x)_$(y)_$(z)_semmap.fth"

    if !isfile(local_fname)
      s3_fname = joinpath(s3_dir_path, local_fname)
      run( `aws s3 cp $s3_fname $local_fname` )
    end
  end

end

function load_relevant_weights(rel_indices)

  sx,sy,sz = size(rel_indices)
  w_arr = Array{Dict{Int,Vector{Float64}}}((sx,sy,sz))

  for z in 1:sz, y in 1:sy, x in 1:sx

    if rel_indices[x,y,z] == (-1,-1,-1)
      w_arr[x,y,z] = Dict{Int,Vector{Float64}}()
      continue
    end

    println((x,y,z))
    lx,ly,lz = rel_indices[x,y,z]
    println((lx,ly,lz))
    fname = "chunk_$(lx)_$(ly)_$(lz)_semmap.fth"
    @time a,w = S.InputOutput.read_semmap(fname)

    w_arr[x,y,z] = w

  end

  w_arr
end

end #module WorkerTasks
