#!/usr/bin/env julia

module pinky_u

include("chunk_u.jl")
include("utils.jl")
include("H5Array.jl")

semantic_dir = "/mnt/data02/jingpeng/pinky/semanticmap/"
semantic_dset_name = "/img"
fname_regexp = r"([0-9]+)-([0-9]+)_([0-9]+)-([0-9]+)_([0-9]+)-([0-9]+)"

function bounds_from_file(filename)

  m = match(fname_regexp, filename)

  coords = map( x -> parse(Int,x), m.captures )

  [coords[1], coords[3], coords[5]] => [coords[2], coords[4], coords[6]]
end


function get_fname_for_index( directory, inds )

  tail = "chunk_$(inds[1])-$(inds[2])_$(inds[3])-$(inds[4])_$(inds[5])-$(inds[6]).h5"

  "$directory/$tail"
end


function init_semantic_arr()

  all_fnames = readdir( semantic_dir )
  filter!( x -> contains(x,"h5"), all_fnames )
  fnames = [ "$(semantic_dir)$fname" for fname in all_fnames ];
  file_bounds = [bounds_from_file(f) for f in fnames];

  H5Array.create_h5arr( fnames, file_bounds, "/img", Float32 )
end


function fetch_chunk( vol, bounds, offset=[0,0,0] )

  i_beg = bounds.first  + offset;
  i_end = bounds.second + offset;

  vol[i_beg[1]:i_end[1],
      i_beg[2]:i_end[2],
      i_beg[3]:i_end[3]]
end


function make_chunked_sem_assignment( seg, sem, seg_bounds,
  class_labels, max_chunk_size )

  processing_chunk_bounds = chunk_u.chunk_bounds( size(seg), max_chunk_size )
  seg_offset = collect(seg_bounds.first) - 1;

  weights = Dict{Int, Vector{Float64}}();
  assignment = Dict{Int,Int}();

  for chunk_bounds in processing_chunk_bounds

    seg_chunk = fetch_chunk( seg, chunk_bounds )
    sem_chunk = fetch_chunk( sem, chunk_bounds, seg_offset )

    @time assignment, weights = utils.make_semantic_assignment(
                                  seg_chunk, sem_chunk,
                                  class_labels, weights )

  end

  assignment, weights
end

end #module end
#-------------------------------------------
