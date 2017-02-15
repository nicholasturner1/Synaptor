#!/usr/bin/env julia

include("dup_u.jl")
include("io_u.jl")

edge_filename = ARGS[1]
outp_filename = ARGS[2]
dist_thr = parse(Int,ARGS[3]) #in nm
res = eval(parse(ARGS[4]))

df = io_u.read_dframe(edge_filename)

println("out_df = dup_u.rm_dups_from_df( df, $dist_thr, $res )")
out_df = dup_u.rm_dups_from_df( df, dist_thr, res )

io_u.write_dframe(out_df, outp_filename)

