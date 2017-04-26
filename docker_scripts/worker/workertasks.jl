module WorkerTasks

using Synaptor; S = Synaptor;
using Synaptor.Consolidation.Continuations
using S3Dicts, BigArrays


#S3 organization
semmap_subdir     = "semmaps"
nh_semmap_subdir  = "nh_semmaps"
ch_edge_subdir    = "ch_edges"
id_map_subdir     = "idmaps"
cont_idmap_subdir = "cont_idmaps"


export semantic_map, expand_semmaps, find_edges
export consolidateids, conscontinuations, consolidatedups
export relabel_seg


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


  #Performing mapping
  @time a, w = S.make_semantic_assignment(seg_chunk, sem_chunk, classes)


  #Writing results to s3
  output_fname = "chunk_$(chx)_$(chy)_$(chz)_semmap.csv"
  s3_output_fname = joinpath(base_s3_path,semmap_subdir,output_fname)
  S.InputOutput.write_semmap(a,w,output_fname)
  run( `aws s3 mv $output_fname $s3_output_fname`)

end


#==========================
JOB2: Semantic Map Expansion
==========================#

function expand_semmaps(taskdict, nh_radius=1)

  #Extracting task args
  sx,sy,sz    = taskdict["max_chunk_i"]
  base_s3_path  = taskdict["base_outpath"]


  #Downloading data
  s3_semmap_dir = joinpath(base_s3_path,semmap_subdir)
  run( `aws s3 cp --recursive $s3_semmap_dir .` )

  @time semmap_arr = load_all_semmaps(sx,sy,sz)
  @time nh_weights = S.neighborhood_semmaps(semmap_arr, 1)
  # @time nh_weights = S.neighborhood_semmaps(semmap_arr, 0)
  @time nh_assigns = map(S.make_assignment, nh_weights)

  #Writing results to s3
  save_all_semmaps(nh_assigns, nh_weights, nh_semmap_subdir)
  s3_output_fname = joinpath(base_s3_path, nh_semmap_subdir)
  run( `aws s3 cp --recursive $nh_semmap_subdir $s3_output_fname` )

end


function load_all_semmaps(sx,sy,sz)

  semmap_arr = Array{Dict{Int,Vector{Float64}}}(sx,sy,sz)

  for z in 1:sz, y in 1:sy, x in 1:sx

    a,w = S.InputOutput.read_semmap("chunk_$(x)_$(y)_$(z)_semmap.csv",2)

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

    output_fname = joinpath(output_dir,"chunk_$(x)_$(y)_$(z)_nhsemmap.csv")
    S.InputOutput.write_semmap(a,w,output_fname)
  end

end


#==========================
JOB3: Chunk Edge Finding
==========================#

ef_params = Dict(
  :volume_map => Dict( :PSDvol => 4 ),
  :CCthresh => 0.2, :SZthresh => 700,
  :dilation => 5, :axon_label => 1,
  :dend_label => 2 )


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
                             "chunk_$(chx)_$(chy)_$(chz)_nhsemmap.csv")
  run( `aws s3 cp $nh_semmap_fname nh_semmap.csv` )
  nh_semmap, weights = S.InputOutput.read_semmap("nh_semmap.csv",2)
  chunk_bbox = S.BBox(chunk_start, chunk_end)
  seg_ch = seg_BA[chunk_bbox]
  S.dilate_by_k!(seg_ch,7)
  sem_ch = sem_BA[chunk_bbox,1:4]


  offset = chunk_start - 1;
  ef = S.SemanticEdgeFinder();
  psdseg_BA = BigArray( S3Dict(psdseg_path) );


  @time (edges, locs, sizes, ccs, conts
  ) = S.process_chunk_w_continuations(sem_ch, seg_ch, ef;
                                      offset=offset,
                                      semmap=nh_semmap,
                                      ef_params... )

  #Writing results to s3
  edge_output_fname = "chunk_$(chx)_$(chy)_$(chz)_ch_edges.csv"
  s3_edge_output_fname = joinpath(base_s3_path,ch_edge_subdir,edge_output_fname)
  S.InputOutput.write_edge_file(edges, locs, sizes, edge_output_fname)
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
  run( `aws s3 cp --recursive $s3_semmap_dir .` )
  edge_arr, locs_arr, sizes_arr = load_all_edges(sx,sy,sz)


  @time id_maps = S.consolidate_ids( map( x -> Set(keys(x)), edge_arr) )
  edges = S.apply_id_maps(edge_arr, id_maps)
  locs  = S.apply_id_maps(locs_arr, id_maps)
  sizes = S.apply_id_maps(sizes_arr, id_maps)


  #Writing results to s3
  edge_output_fname = "consolidated_edges_wo_conts.csv"
  s3_edge_output_fname = joinpath(base_s3_path,edge_output_fname)
  S.InputOutput.write_edge_file(edges, locs, sizes, edge_output_fname)
  run( `aws s3 cp $edge_output_fname $s3_edge_output_fname` )

  save_all_idmaps(id_maps, id_map_subdir)
  s3_output_fname = joinpath(base_s3_path,id_map_subdir)
  run( `aws s3 cp --recursive $id_map_subdir $s3_output_fname` )

  next_id = maximum(keys(edges)) + 1
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

  for z in 1:sz, y in 1:sy, x in 1:sx

    e,l,s = S.InputOutput.read_edge_file("chunk_$(x)_$(y)_$(z)_ch_edges.csv",3)

    edge_arr[x,y,z] = e
    locs_arr[x,y,z] = l
    sizes_arr[x,y,z] = s
  end

  edge_arr, locs_arr, sizes_arr
end


function save_all_idmaps(id_maps, subdir_name)

  if !isdir(subdir_name)  mkdir(subdir_name)  end

  sx,sy,sz = size(id_maps)

  for z in 1:sz, y in 1:sy, x in 1:sx
    map = id_maps[x,y,z]

    output_fname = joinpath(subdir_name,"chunk_$(x)_$(y)_$(z)_idmap.csv")
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
  s3_ch_edge_dir = joinpath(base_s3_path,ch_edge_subdir)
  run( `aws s3 cp --recursive $s3_ch_edge_dir .` )
  s3_semmap_dir = joinpath(base_s3_path,nh_semmap_subdir)
  run( `aws s3 cp --recursive $s3_semmap_dir .` )
  next_id_fname = joinpath(base_s3_path,"next_id")
  run( `aws s3 cp $next_id_fname .` )

  cont_arr = load_all_continuations(sx,sy,sz)
  semmap_arr = load_all_nh_semmaps(sx,sy,sz)
  next_id = load_next_id()
  size_thr = ef_params[:SZthresh]


  (edges, locs, sizes, idmaps
  ) = S.consolidate_continuations(cont_arr, semmap_arr, size_thr,
                                  next_id, total_vol, chunk_shape,
                                  offset, boundtype)

  #Writing results to s3
  edge_output_fname = "continuation_edges.csv"
  s3_edge_output_fname = joinpath(base_s3_path,edge_output_fname)
  S.InputOutput.write_edge_file(edges, locs, sizes, edge_output_fname)
  run( `aws s3 cp $edge_output_fname $s3_edge_output_fname` )

  save_all_idmaps(idmaps, cont_idmap_subdir)
  s3_output_fname = joinpath(base_s3_path,cont_idmap_subdir)
  run( `aws s3 cp --recursive $cont_idmap_subdir $s3_output_fname` )
end


function load_all_continuations(sx,sy,sz)

  cont_arr = Array{Vector{Continuation}}(sx,sy,sz)

  for z in 1:sz, y in 1:sy, x in 1:sx

    cs = S.InputOutput.read_continuations("chunk_$(x)_$(y)_$(z)_ch_conts.h5")

    cont_arr[x,y,z] = cs
  end

  cont_arr
end

function load_all_nh_semmaps(sx,sy,sz)

  semmap_arr = Array{Dict{Int,Int}}(sx,sy,sz)

  for z in 1:sz, y in 1:sy, x in 1:sx

    a,w = S.InputOutput.read_semmap("chunk_$(x)_$(y)_$(z)_nhsemmap.csv",2)

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
  whole_edge_fname = "consolidated_edges_wo_conts.csv"
  s3_edges_wo_continuations = joinpath(base_s3_path,whole_edge_fname)
  run( `aws s3 cp $s3_edges_wo_continuations .` )

  cont_edge_fname = "continuation_edges.csv"
  s3_continuation_edge_fname = joinpath(base_s3_path,cont_edge_fname)
  run( `aws s3 cp $s3_continuation_edge_fname .`)

  edges, locs, sizes = S.InputOutput.read_edge_file(whole_edge_fname, 3)
  ec, lc, sc = S.InputOutput.read_edge_file(cont_edge_fname, 3)

  merge!(edges, ec)
  merge!(locs, lc)
  merge!(sizes, sc)

  @time new_es, new_ls, new_ss, idmap = S.consolidate_dups(edges, locs, sizes,
                                                           dist_thr, res)

  #Writing results to s3
  final_edge_fname = "final_edges.csv"
  S.InputOutput.write_edge_file(new_es, new_ls, new_ss, final_edge_fname)
  s3_final_edge_fname = joinpath(base_s3_path, final_edge_fname)
  run( `aws s3 cp $final_edge_fname $s3_final_edge_fname` )

  dedup_idmap_fname = "dedup_idmap.csv"
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
  seg_s3_path   = taskdict["seg_path"]
  sem_s3_path   = taskdict["sem_path"]
  base_s3_path  = taskdict["base_outpath"]

  seg_BA = BigArray(S3Dict( seg_s3_path ))
  sem_BA = BigArray(S3Dict( sem_s3_path ))

  #Downloading data
  whole_seg_idmap_path = joinpath(base_s3_path,id_map_subdir,
                                  "chunk_$(chx)_$(chy)_$(chz)_idmap.csv")
  run( `aws s3 cp $whole_seg_idmap_path whole_seg_idmap.csv` )

  cont_idmap_path = joinpath(base_s3_path,cont_idmap_subdir,
                            "chunk_$(chx)_$(chy)_$(chz)_idmap.csv")
  run( `aws s3 cp $cont_idmap_path continuation_idmap.csv` )

  dedup_idmap_fname = "dedup_idmap.csv"
  s3_dedup_idmap_fname = joinpath(base_s3_path, dedup_idmap_fname)
  run( `aws s3 cp $s3_dedup_idmap_fname $dedup_idmap_fname`)


  whole_idmap = S.InputOutput.read_idmap("whole_seg_idmap.csv")
  cont_idmap = S.InputOutput.read_idmap("continuation_idmap.csv")
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


end #module WorkerTasks
