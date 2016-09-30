#!/usr/bin/env julia
__precompile__()

#=
  I/O Utils - io_u.jl
=# 
module io_u

using HDF5

export read_h5
export save_edge_file
export read_map_file, write_map_file


#using HDF5 here
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


#module end
end
