module ContinuationIO

using HDF5

using ...Consolidation.Continuations

export write_continuation, write_continuations
export read_continuation, read_continuations


function write_continuations(output_fname, continuations::Array{Continuation})
  h5open(output_fname, "w") do f
    for (i,c) in enumerate(continuations)  write_continuation(f,c,i)  end
  end
end


function write_continuations( output_fname, continuations... )
  h5open(output_fname, "w") do f
    for (i,c) in enumerate(continuations)  write_continuation(f,c,i)  end
  end
end

function write_continuation( f, continuation, key=-1 )

  if key == -1  keystr = ""
  else          keystr = "$key/"
  end

  #Easy stuff
  write(f, "$(keystr)segid", continuation.segid)
  write(f, "$(keystr)voxels", continuation.voxels)
  write(f, "$(keystr)num_voxels", continuation.num_voxels)
  write(f, "$(keystr)loc", continuation.location)
  write(f, "$(keystr)bbox", collect(continuation.bbox))

  #Less easy stuff
  write_overlaps(f, keystr, continuation.overlaps)
  write_face(f, keystr, continuation.face)

end


function write_overlaps(f, keystr, overlaps)

  num_overlaps = length(overlaps)

  output_arr = zeros(Int,(num_overlaps, 2))

  i = 1
  for (i,p) in enumerate(overlaps)
    output_arr[i,1] = first(p)
    output_arr[i,2] = last(p)
  end

  write(f, "$(keystr)overlaps", output_arr)

end


function write_face(f, keystr, face)
  write(f, "$(keystr)face", [Int(face.axis), Int(face.hi)])
end


function read_continuations(input_fname, ks=Int[])

  res = Continuation[]
  if length(ks) == 0
    f = h5open(input_fname)
    candidate_keys = names(f)
    close(f)

    try

      ks = map( x -> parse(Int,x), candidate_keys )
      h5open(input_fname) do f
        res = [read_continuation(f, k) for k in ks]
      end

    catch err

      println(err)
      h5open(input_fname) do f
        res = [read_continuation(f)]
      end
    end

  else

    h5open(input_fname) do f
      res = [read_continuation(f, k) for k in ks]
    end

  end

  res
end


function read_continuation(f, key=-1)

  if key == -1  keystr = ""
  else          keystr = "$key/"
  end

  segid      = read(f, "$(keystr)segid")
  voxels     = read(f, "$(keystr)voxels")
  if length(voxels) == 0  voxels = reshape(voxels, (0,3))  end

  num_voxels = read(f, "$(keystr)num_voxels")
  loc        = read(f, "$(keystr)loc")

  bbox_inds  = read(f, "$(keystr)bbox")
  bbox = Continuations.BBox(bbox_inds...)
  #bbox = Continuations.BBox(0,0,0,0,0,0)

  overlaps = read_overlaps(f, keystr)
  face     = read_face(f, keystr)

  Continuation(segid, voxels, overlaps, face, num_voxels, loc, bbox)
end


function read_overlaps(f, keystr)

  overlap_arr = read(f, "$(keystr)overlaps")

  Dict(overlap_arr[i,1] => overlap_arr[i,2]
       for i in 1:size(overlap_arr,1))
end


function read_face(f, keystr)

  face_vec = read(f, "$(keystr)face")

  Face(face_vec[1], Bool(face_vec[2]))
end


end #module ContinuationIO
