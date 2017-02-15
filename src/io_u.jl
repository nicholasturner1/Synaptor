#!/usr/bin/env julia

#=
  I/O Utils - io_u.jl
=#
module io_u

include("pinky_u.jl")
include("BigWrappers.jl")
using HDF5

export read_h5
export save_edge_file
export read_map_file, write_map_file
export save_voxel_file, read_voxel_file
export read_id_map_lines
export create_seg_dset


#using HDF5
"""
    read_h5( filename, read_whole_dataset=true, h5_dset_name="/main" )
"""
function read_h5( filename, read_whole_dataset=true, h5_dset_name="/main" )
  #Assumed to be an h5 file for now
  if read_whole_dataset
    d = h5read( filename, h5_dset_name );
  else
    f = h5open( filename );
    d = f[ h5_dset_name ];
  end

  return d;
end


"""

    write_h5( dset, filename, h5_dset_name="/main" )

  Makes a new h5file containing dset under the name h5_dset_name
"""
function write_h5( dset, filename, h5_dset_name="/main" )
  if isfile(filename)
    rm(filename)
  end

  HDF5.h5write(filename, "/main", dset);
end


"""

    save_edge_file( edges, locations, segids, output_filename )

  Saves a file detailing the information on synapses discovered
  through the postprocessing. Writes the following semicolon-separated
  format:

  synapse_id ; (axon_id, dendrite_id) ; synapse center-of-mass coordinate
"""
function save_edge_file( edges, locations, segids, output_filename )

  open( output_filename, "w+" ) do f

    for i in 1:length(edges)
      edge = edges[i]
      location = locations[i]
      segid = segids[i]

      write(f, "$segid ; $(edge) ; $(location) \n")
    end

  end

end


"""

    save_voxel_file( voxels, ids )

  Writes a file which specifies each synapse coordinate as a
  separate line, along with its segment id in the first column.
"""
function save_voxel_file( voxels::Vector{Vector{Tuple{Int,Int,Int}}}, ids,
  output_filename )

  @assert length(voxels) == length(ids)

  open( output_filename, "w+" ) do f

    for i in 1:length(voxels)
      segid = ids[i]
      for v in voxels[i]
        write(f, "$segid, $(join(v,",")) \n")
      end

    end

  end#open() do f

end


"""

    read_voxel_file

  Reads the files produced by save_voxel_file. Returns a mapping
  from coordinate (Vector{Int}) to segid
"""
function read_voxel_file( input_filename, offset=[0,0,0] )

  res = Dict{Vector{Int},Int}();

  open(input_filename) do f

    for ln in eachline(f)

      segid, x,y,z = map(x -> parse(Int,x), split(ln,","))

      res[[x+offset[1],
           y+offset[2],
           z+offset[3]]] = segid

    end#for ln
  end#do f

  res

end


"""
    write_map_file( output_filename, dicts... )

  Take an iterable of dictionaries which all have the same
  keys. Write a file in which each line takes the form

  key;val1;val2... for the number of dictionaries
"""
function write_map_file( output_filename, dicts... )

  open(output_filename, "w+") do f
    if length(dicts) > 0
    for k in keys(dicts[1])

      vals = ["$(d[k]);" for d in dicts ];
      write(f, "$k;$(vals...)\n" )

    end #for k
    end #if length
  end #open(fname)
end


"""

    read_map_file( input_filename, num_columns, sep=";" )

  Reads in map files written by write_map_file. Returns the first
  num_columns dicts stored within the file, but will break if you specify
  too many dicts to read.
"""
function read_map_file( input_filename, num_columns, sep=";" )

  dicts = [Dict() for i=1:num_columns];

  open(input_filename) do f

    for ln in eachline(f)

      fields = map(x -> eval(parse(x)), split(ln, sep));

      key = fields[1]

      for d in 1:length(dicts)
        dicts[d][key] = fields[1+d];
      end

    end#for ln

  end#do f

  dicts
end


function read_single_map(filename)
  read_map_file(filename,1)[1]
end


"""

    read_id_map_lines( input_filename, sep=";" )

  Reads a file which has an id number in the first field,
  and returns a mapping from that id to the rest of the
  line as a string.
"""
function read_id_map_lines( input_filename, sep=";" )

  res = Dict{Int,AbstractString}();

  open(input_filename) do f

    for ln in eachline(f)

      fields = split(ln,sep)

      lineid = parse(Int, fields[1])
      rest = join(fields[2:end],sep)

      res[lineid] = rest

    end#for ln

  end#do f

  res
end


#using HDF5
"""

    create_seg_dset( fname, vol_size, chunk_size, dset_name="/synseg",
      dtype=UInt32, compress_level=3 )

  Initializes an empty HDF5 dataset within a file under the given
  name, shape, chunk shape, type, and compresion level.
"""
function create_seg_dset( fname, vol_size, chunk_size,
  dset_name="/synseg", dtype=UInt32, compress_level=3 )

  f = h5open( fname, "w" )

  dset = d_create(f, dset_name, datatype(dtype), dataspace(vol_size...),
                  "chunk", chunk_size, "compress", compress_level )

  dset
end


#using HDF5
"""

    import_dataset( seg_fname, net_out_fname )

  Imports a dataset as a BigArray wrapper (put repo URL here) or
  an HDF5 file, possibly reading the entire file into RAM. Attempts
  to read by filename extension.
"""
function import_dataset( fname, incore )

  if fname == nothing
    pinky_u.init_semantic_arr()
  elseif ismatch( r".*.h5", fname )
    read_h5(fname, incore)
  else
    BigWrappers.BigWrapper(fname)
  end
end


#using HDF5
"""

    read_MST( seg_fname, threshold )

  Reads in an mst mapping from an h5 file assuming more than I should for now
"""
function read_MST( seg_fname, threshold )

  segmentPairs = h5read( seg_fname, "dend" )
  segmentPairAffinities = h5read( seg_fname, "dendValues" )

  read_MST( segmentPairs, segmentPairAffinities, threshold )
end


"""

    read_MST( segmentPairs, segmentPairAffinities, threshold )

  Reads in the MST from segmentation files thresholded at the given
  value. Only contains key value pairs for a node if it is not a root node
"""
function read_MST( segmentPairs, segmentPairAffinities, threshold )

  assignment = Dict{Int,Int}();

  for i in eachindex( segmentPairAffinities )

    if segmentPairAffinities[i] > threshold
      child, parent = segmentPairs[i,:];
      assignment[ child ] = parent #get( assignment, parent, parent )
    end

  end


  #still not 100% sure why we should need to consolidate
  # given proper ordering, but this should work for now
  for (k,v) in assignment
    ks = [k]
    next_v = get(assignment,v,v)

    while v != next_v
      push!(ks,v)
      v, next_v = next_v, get(assignment,next_v,next_v)
    end

    #next_v is now a root
    for k in ks assignment[k] = next_v end
   end

  assignment
end


function read_dframe( input_filename, sep=';' )

  raw = readdlm(input_filename,sep)
  raw = raw[:,1:(end-1)]
  for i in 1:size(raw,2)
    #readdlm returns Ints or strings
    if typeof(raw[1,i]) == Int continue end
    raw[:,i] = map(x -> eval(parse(x)), raw[:,i])
  end

  raw
end


function write_dframe( df, output_filename, sep=";" )

  open(output_filename, "w+") do f

    for r in 1:size(df,1)
      fields = map(string,df[r,:])
      write(f,"$(join(fields,sep))\n")
    end #for r
  end #open(fname)
end


#module end
end
