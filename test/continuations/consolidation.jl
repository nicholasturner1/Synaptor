module ConsolidationTests

using Base.Test

using ....Synaptor.Consolidation.Continuations
using ....Synaptor.Consolidation.ConsolidateContinuations
#using LightGraphs

@testset "Consolidation" begin


test_c_arr = Array{Vector{Continuation},3}(2,2,2)

cs_1_1_1 = [Continuation(1,[2 2 2;],Dict(1=>1),Face(1,true),5,[2,2,2]),
            Continuation(1,[2 2 2;],Dict(1=>1),Face(2,true),5,[2,2,2]),
            Continuation(1,[2 2 2;],Dict(1=>1),Face(3,true),5,[2,2,2])]
cs_1_2_1 = [Continuation(1,[2 1 2;],Dict(2=>2),Face(2,false),20,[2,3,2])]
cs_2_1_1 = [Continuation(1,[1 1 1;],Dict(3=>3,4=>4),Face(1,false),30,[3,1,1]),
            Continuation(1,[1 1 1;],Dict(3=>3,4=>4),Face(2,false),30,[3,1,1]),
            Continuation(1,[1 1 1;],Dict(3=>3,4=>4),Face(3,false),30,[3,1,1])]

for i in eachindex(test_c_arr)  test_c_arr[i] = Continuation[]  end

test_c_arr[1,1,1] = cs_1_1_1
test_c_arr[1,2,1] = cs_1_2_1
test_c_arr[2,1,1] = cs_2_1_1


merged_cs, c_locs = ConsolidateContinuations.merge_continuations(test_c_arr)


test_semmap1 = [Dict( 1=>1, 2=>2, 3=>1, 4=>2 ) for i in 1:2, j in 1:2]
test_semmap2 = [Dict( 1=>1, 2=>2, 3=>3, 4=>2 ) for i in 1:2, j in 1:2]
test_chunk_shape = [2,2,2]

#---------------------
#test1

filtered, semmaps, idmap = ConsolidateContinuations.filter_continuations(merged_cs,test_semmap1,
                                                     20,1,[2,2,2])

@test length(filtered) == 2
@test idmap == [1,2]

expanded_idmaps = ConsolidateContinuations.expand_id_maps(idmap, c_locs, size(test_c_arr))

@test expanded_idmaps[1,1,1][1] == expanded_idmaps[1,2,1][1] == 1
@test expanded_idmaps[2,1,1][1] == 2

edges, locs, sizes = ConsolidateContinuations.extract_info(filtered, semmaps)

@test edges[1] == (1,2)
@test locs[1] == [2,3,2]
@test sizes[1] == 25

@test edges[2] == (3,4)
@test locs[2]  == [3,1,1]
@test sizes[2] == 30

@test length(edges) == length(locs) == length(sizes) == 2

#---------------------
#test2

filtered, semmaps, idmap = ConsolidateContinuations.filter_continuations(merged_cs,test_semmap1,
                                                     25,1,[2,2,2])

@test length(filtered) == 1
@test idmap == [0,1]

expanded_idmaps = ConsolidateContinuations.expand_id_maps(idmap, c_locs, size(test_c_arr))

@test expanded_idmaps[1,1,1][1] == expanded_idmaps[1,2,1][1] == 0
@test expanded_idmaps[2,1,1][1] == 1

edges, locs, sizes = ConsolidateContinuations.extract_info(filtered, semmaps)

@test edges[1] == (3,4)
@test locs[1]  == [3,1,1]
@test sizes[1] == 30 

@test length(edges) == length(locs) == length(sizes) == 1

#---------------------
#test3

filtered, semmaps, idmap = ConsolidateContinuations.filter_continuations(merged_cs,test_semmap2,
                                                     25,1,[2,2,2])

@test length(filtered) == 0
@test idmap == [0,0]

expanded_idmaps = Consolidation.expand_id_maps(idmap, c_locs, size(test_c_arr))

@test expanded_idmaps[1,1,1][1] == expanded_idmaps[1,2,1][1] == expanded_idmaps[2,1,1][1] == 0

edges, locs, sizes = Consolidation.extract_info(filtered, semmaps)

@test isempty(edges)
@test isempty(locs)
@test isempty(sizes)

#---------------------
#test4

filtered, semmaps, idmap = Consolidation.filter_continuations(merged_cs,test_semmap1,
                                                     10,3,[2,2,2])

@test length(filtered) == 2
@test idmap == [3,4]

expanded_idmaps = Consolidation.expand_id_maps(idmap, c_locs, size(test_c_arr))

@test expanded_idmaps[1,1,1][1] == expanded_idmaps[1,2,1][1] == 3
@test expanded_idmaps[2,1,1][1] == 4

edges, locs, sizes = Consolidation.extract_info(filtered, semmaps)

@test edges[3] == (1,2)
@test locs[3]  == [2,3,2]
@test sizes[3] == 25

@test edges[4] == (3,4)
@test locs[4]  == [3,1,1]
@test sizes[4] == 30

@test length(edges) == length(locs) == length(sizes) == 2

end #testset "Consolidation"

end #module ConsolidationTests
