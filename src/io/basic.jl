module BasicIO


export read_edge_file, write_edge_file
export read_semmap, write_semmap
export write_idmap, read_idmap


function read_csv(fname, T::DataType)

  res = nothing
  open(fname) do f
    try
      res = readdlm(f,',',T)
    catch
      #generally means there are no lines in the file,
      # but just to be careful
      warn("Error reading file $fname, returning blank contents")
      res = []
    end
  end

  res
end


function read_edge_pair_file(fname)

  arr = read_csv(fname, Int)

  if length(arr) == 0 return arr end

  @assert size(arr,2) == 2

  [(arr[i,1],arr[i,2]) for i in 1:size(arr,1)]
end


write_edge_file(edges, fname) = write_map_file(fname, edges)
write_edge_file(edges, locs, fname) = write_map_file(fname, edges, locs)
write_edge_file(edges, locs, sizes, fname) = write_map_file(fname, edges, locs, sizes)

read_edge_file(fname, num_outputs) = safe_read_map_file(fname, num_outputs)

"""

    read_map_file( input_fname; delim=';' )

  Reads in map files as written by write_map_file.
"""
function read_map_file( input_fname; delim=';' )

  num_fields = 0 #init
  Ts = DataType[];

  open(input_fname) do f

    if eof(f) return [] end

    first_ln = readline(f)
    fields = map(x -> eval(parse(x)), split(first_ln,"$delim"))
    num_fields = length(fields)-1 #-1 for key
    Ts = map(typeof, fields)
  end

  dicts = [Dict{Ts[1],Ts[i+1]}() for i=1:num_fields];

  open(input_fname) do f

    for ln in eachline(f)

      fields = map(x -> eval(parse(x)), split(ln,"$delim"));
      key = fields[1]

      for i in 1:length(dicts)  dicts[i][key] = fields[i+1]  end

    end #for ln

  end#open(input_fname)

  dicts
end


function safe_read_map_file(fname, num_outputs)
  res = read_map_file(fname)

  if     length(res) == num_outputs    return res
  elseif length(res) == 0              return [Dict() for i in 1:num_outputs]
  else                                 return res
  end
end

"""

    write_map_file( output_fname, dicts...; delim=';' )

  Takes a collection of dictionaries which are assumed to have the
  same keys (or, at least those of the first dict). Writes a file
  in which each line takes the form

  key;val1;val2... for the number of dictionaries
"""
function write_map_file( output_fname, dicts...; delim=';' )

  open(output_fname, "w+") do f
    if length(dicts) > 0
    for k in keys(dicts[1])

      valstring = join(["$(d[k])" for d in dicts ], delim);
      write(f, "$k;$valstring\n" )

    end #for k
    end #if length
  end #open(fname)

end


"""

    read_semmap(input_fname)

  Reads a semicolon-delimited csv file as a pair of Dicts representing
  the result of a semantic mapping
"""
read_semmap(input_fname, num_outputs) = safe_read_map_file(input_fname, num_outputs)


"""

    write_semmmap(assignment, [weights], output_fname)

  Saves a semantic id map as a semicolon-delimited csv file
"""
write_semmap(a,w,output_fname) = write_map_file(output_fname, a,w)
write_semmap(a,output_fname) = write_map_file(output_fname, a)

"""

    write_semmmap(assignment, [weights], output_fname)

  Saves an id map as a semicolon-delimited csv file
"""
write_idmap(m, output_fname) = write_map_file(output_fname, m)

read_idmap(input_fname) = safe_read_map_file(input_fname, 1)[1]

end #module BasicIO
