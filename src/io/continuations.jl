module ContinuationIO

using HDF5

using ...Consolidation.Continuations

export write_continuation, write_continuations
export read_continuation, read_continuations


function write_continuations(output_fname, continuations::Array{Continuation})
  f = h5open(output_fname, "w")
  close(f)
  for (i,c) in enumerate(continuations)  write_continuation(output_fname,c,i)  end
end


function write_continuations( output_fname, continuations... )
  f = h5open(output_fname, "w")
  close(f)
  for (i,c) in enumerate(continuations)  write_continuation(output_fname,c,i)  end
end

function write_continuation( output_fname, continuation, key=-1 )

  if key == -1  keystr = ""
  else          keystr = "$key/"
  end

  #Easy stuff
  h5write(output_fname, "$(keystr)segid", continuation.segid)
  h5write(output_fname, "$(keystr)voxels", continuation.voxels)
  h5write(output_fname, "$(keystr)num_voxels", continuation.num_voxels)
  h5write(output_fname, "$(keystr)loc", continuation.location)
  h5write(output_fname, "$(keystr)bbox", collect(continuation.bbox))

  #Less easy stuff
  write_overlaps(output_fname, keystr, continuation.overlaps)
  write_face(output_fname, keystr, continuation.face)

end


function write_overlaps(output_fname, keystr, overlaps)

  num_overlaps = length(overlaps)

  output_arr = zeros(Int,(num_overlaps, 2))

  i = 1
  for (i,p) in enumerate(overlaps)
    output_arr[i,1] = first(p)
    output_arr[i,2] = last(p)
  end

  h5write(output_fname, "$(keystr)overlaps", output_arr)

end


function write_face(output_fname, keystr, face)
  h5write(output_fname, "$(keystr)face", [Int(face.axis), Int(face.hi)])
end


function read_continuations(input_fname, ks=Int[])

  res = Continuation[]
  if length(ks) == 0
    f = h5open(input_fname)
    candidate_keys = names(f)

    try

      ks = map( x -> parse(Int,x), candidate_keys )
      res = [read_continuation(input_fname, k) for k in ks]

    catch err

      println(err)
      res = [read_continuation(input_fname)]
    end

  else

    res = [read_continuation(input_fname, k) for k in ks]

  end

  res
end


function read_continuation(input_fname, key=-1)

  if key == -1  keystr = ""
  else          keystr = "$key/"
  end

  segid      = h5read(input_fname, "$(keystr)segid")
  voxels     = h5read(input_fname, "$(keystr)voxels")
  if length(voxels) == 0  voxels = reshape(voxels, (0,3))  end

  num_voxels = h5read(input_fname, "$(keystr)num_voxels")
  loc        = h5read(input_fname, "$(keystr)loc")

  bbox_inds  = h5read(input_fname, "$(keystr)bbox")
  bbox = Continuations.BBox(bbox_inds...)
  #bbox = Continuations.BBox(0,0,0,0,0,0)

  overlaps = read_overlaps(input_fname, keystr)
  face     = read_face(input_fname, keystr)

  Continuation(segid, voxels, overlaps, face, num_voxels, loc, bbox)
end


function read_overlaps(input_fname, keystr)

  overlap_arr = h5read(input_fname, "$(keystr)overlaps")

  Dict(overlap_arr[i,1] => overlap_arr[i,2]
       for i in 1:size(overlap_arr,1))
end


function read_face(input_fname, keystr)

  face_vec = h5read(input_fname, "$(keystr)face")

  Face(face_vec[1], Bool(face_vec[2]))
end


end #module ContinuationIO
