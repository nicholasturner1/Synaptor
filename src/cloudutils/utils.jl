module Utils


export parse_coord_msg


function parse_coord_msg(msg::String)
  return map(x -> parse(Int,x), split(msg," "))
end

end #module Utils
