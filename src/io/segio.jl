module SegIO

using ...Chunking

using HDF5

export create_seg_dset
export write_in_chunks


function create_seg_dset(fname, vol_size, chunk_size,
                         dset_name="/main",dtype=UInt32,
                         compress_level=3)

  f = h5open(fname, "w")

  dset = d_create(f, dset_name, datatype(dtype), dataspace(vol_size...),
                  "chunk", chunk_size, "compress", compress_level)

  dset
end

function write_in_chunks( output_arr, chunks, chunk_shape )

  chunk_bboxes = Chunking.chunk_bounds(size(output_arr), chunk_shape)

  @assert length(chunks) == length(chunk_bboxes)

  for (i,chunk) in enumerate(chunk_bboxes)

    output_arr[chunk] = chunks[i]
  end

end

end #ChunksIO
