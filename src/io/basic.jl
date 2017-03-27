module BasicIO


export read_edge_file


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


function read_edge_file(fname)

  arr = read_csv(fname, Int)

  if length(arr) == 0 return arr end

  @assert size(arr,2) == 2

  [(arr[i,1],arr[i,2]) for i in 1:size(arr,1)]
end


end #module BasicIO
