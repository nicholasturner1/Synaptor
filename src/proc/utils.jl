
module Utils

export collect_params

collect_params(p) = Dict( name => val for (name,val) in p )

end #module Utils
