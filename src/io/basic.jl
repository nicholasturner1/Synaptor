module BasicIO


export read_edge_file


function read_csv(fname, T::DataType)

  res = nothing
  open(fname) do f
    res = readdlm(f,',',T)
  end

  res
end


function read_edge_file(fname)

  arr = read_csv(fname, Int)

  @assert size(arr,2) == 2

  [(arr[i,1],arr[i,2]) for i in 1:size(arr,1)]
end


end #module BasicIO
