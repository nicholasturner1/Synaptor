module DilationTests


using Base.Test


import ....Synaptor.SegUtils.Dilation


@testset "Dilation" begin


@testset "manhattan_distance2D!" begin

  test_input1 = zeros(Int,(5,5,5))
  test_input1[3,3,:] = 1

  md = Dilation.manhattan_distance2D!(test_input1)

  @test maximum(md) == 4
  @test count(x -> x == 1, md) == 20
  @test count(x -> x == 0, md) == 5
  @test count(x -> x == 1, test_input1)  == 125

end


@testset "dilate_by_k!" begin

  test_input1 = zeros(Int,(5,5,5))
  test_input1[3,3,:] = 1

  Dilation.dilate_by_k!(test_input1,1)

  @test count(x -> x == 1, test_input1) == 25
  @test count(x -> x == 0, test_input1) == 100

  Dilation.dilate_by_k!(test_input1,1)

  @test count(x -> x == 1, test_input1) == 65
  @test count(x -> x == 0, test_input1) == 60

end

end #testset Dilation

end #module DilationTests
