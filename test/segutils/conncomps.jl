module ConnCompsTests


using Base.Test


import ....Synaptor.SegUtils.ConnComps


@testset "Connected Components" begin

test_input1 = zeros(3,3,3)
test_input1[1,1,1] = 1
test_input1[2,2,2] = 1
test_input1[3,3,3] = 1


@testset "connected_component3D" begin

  cc1, _ = ConnComps.connected_component3D(test_input1, (1,1,1), 0.5)
  cc2, _ = ConnComps.connected_component3D(test_input1, (2,2,2), 0.5)
  cc3, _ = ConnComps.connected_component3D(test_input1, (3,3,3), 0.5)

  @test findn(cc1) == ([1],[1],[1])
  @test findn(cc2) == ([2],[2],[2])
  @test findn(cc3) == ([3],[3],[3])

end


@testset "connected_components3D" begin

  test_input = [1 0 1 0 1];

  cc = ConnComps.connected_components3D(test_input1)

  @test findn(cc) == ([1,2,3],[1,2,3],[1,2,3])
  @test Set(unique(cc)) == Set([0,1,2,3])

end


end #@testset Connected Components


end #module ConnCompsTests
