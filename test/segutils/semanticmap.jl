module SemanticMapTests


using Base.Test


import ....Synaptor.SegUtils.SemanticMap

@testset "SemanticMap" begin


test_seg = zeros(Int,(3,3,3))
test_seg[1:2,1:2,1:2] = 1
test_seg[:,:,3] = 2

test_weight = zeros(Float64,(3,3,3,2))
test_weight[:,:,:,1] = 1
test_weight[:,:,:,2] = 2

classes = [1,2]


@testset "make_semantic_assignment" begin

  a, w = SemanticMap.make_semantic_assignment(test_seg, test_weight, classes )

  @test a[1] == 2
  @test a[2] == 2

  @test w[1] == [8,16]
  @test w[2] == [9,18]

  #weight dict modification
  a, w = SemanticMap.make_semantic_assignment(test_seg, test_weight, classes, w )

  @test w[1] == [16,32]
  @test w[2] == [18,36]

end


@testset "addsemweights" begin

  sw1 = Dict( i => [i] for i in 1:3 )
  sw2 = Dict( i => [i] for i in 4:6 )

  #disjoint keys
  res1 = SemanticMap.addsemweights(sw1,sw2)

  @test res1 == Dict( i => [i] for i in 1:6 )

  #same keys
  res2 = SemanticMap.addsemweights(sw1,sw1)

  @test res2 == Dict( i => [2i] for i in 1:3 )

end


@testset "neighborhood_semmaps" begin

  a = Array{Dict{Int,Vector{Int}},3}(5,5,5)
  for i in eachindex(a)  a[i] = Dict(i => [i])  end

  nhoods0 = SemanticMap.neighborhood_semmaps(a,0)
  nhoods1 = SemanticMap.neighborhood_semmaps(a,1)
  nhoods2 = SemanticMap.neighborhood_semmaps(a,2)

  @test nhoods0 == a
  @test length(nhoods1[1,1,1]) == 8
  @test length(nhoods1[3,3,3]) == 27
  @test length(nhoods1[5,5,5]) == 8
  @test Set(keys(nhoods1[1,1,1])) == Set(union(map(keys,a[1:2,1:2,1:2])...))

  @test length(nhoods2[1,1,1]) == 27
  @test length(nhoods2[3,3,3]) == 125
  @test length(nhoods2[5,5,5]) == 27
  @test Set(keys(nhoods2[1,1,1])) == Set(union(map(keys,a[1:3,1:3,1:3])...))

end


end #@testset SemanticMap


end #module SemanticMapTests
