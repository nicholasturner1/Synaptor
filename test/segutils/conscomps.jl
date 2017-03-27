
module ConsCompsTests

using Base.Test

import ....Synaptor.SegUtils.ConsComps


@testset "find_components_within_dist" begin
#INCOMPLETE

  pt0 = [0,0]
  pt1 = [1,0]
  pt2 = [5,5]
  
  res1 = [1,1]
  res0 = [0,0]
  res2 = [100,200]

  ccs = ConsComps.find_components_within_dist( [pt0,pt1,pt2], res1, 2 )

  @test length(ccs) == 2
  @test ccs[1] == [1,2]
  @test ccs[2] == [3]

end


@testset "dists_within_locs" begin
#INCOMPLETE

  pt0 = [0,0]
  pt1 = [1,0]
  pt2 = [0,1]
  pt3 = [1,1]

  res1 = [1,1]
  res2 = [2,1]
  res3 = [0,0]

  d, p = ConsComps.dists_within_locs( [pt0,pt1], res1 )
  
  @test d[1] == 1.0
  @test p[1] == (1,2)
  @test length(d) == length(p) == 1

end


@testset "add_ccs_to_map!" begin

  mapping = Dict()

  ccs1 = [[1,2,3],[4]]
  ccs2 = [[3,2,1],[5]]

  ids1 = [1,2,3,4,5]
  ids2 = [1000,2000,3000,4000,5]

  ConsComps.add_ccs_to_map!(mapping, ids1, ccs1)

  @test mapping[1] == 1
  @test mapping[2] == 1
  @test mapping[3] == 1
  @test mapping[4] == 4

  ConsComps.add_ccs_to_map!(mapping, ids2, ccs1)

  @test mapping[1] == 1
  @test mapping[1000] == 1000
  @test mapping[2000] == 1000
  @test mapping[3000] == 1000
  @test mapping[4000] == 4000

  ConsComps.add_ccs_to_map!(mapping, ids1, ccs2)

  @test mapping[1] == 1
  @test mapping[2] == 1
  @test mapping[3] == 1
  @test mapping[5] == 5

  ConsComps.add_ccs_to_map!(mapping, ids2, ccs2)

  @test mapping[1000] == 1000
  @test mapping[2000] == 1000
  @test mapping[3000] == 1000
  @test mapping[5] == 5

end


end #module ConsCompsTests
