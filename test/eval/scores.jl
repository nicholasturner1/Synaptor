
module ScoresTests 

using Base.Test

import ....Synaptor.Eval.Scores


@testset "precision" begin

  l1 = [1,2,3,4]
  l2 = [2,3,4]
  l3 = [1,1,2,3,4]
  l0 = []

  #basic stuff
  @test Scores.precision(l1,l2) == (0.75, [true,false,false,false])
  @test Scores.precision(l2,l1) == (1,    [false,false,false,false])
  @test Scores.precision(l1,l0) == (0,    [true,true,true,true])
  @test Scores.precision(l0,l1) == (1,    [])

  #duplicates
  @test Scores.precision(l3,l1,true)  == (0.8,  [false,true,false,false,false])
  @test Scores.precision(l3,l1,false) == (1,    [false,false,false,false])
  @test Scores.precision(l3,l2,true)  == (0.6,  [true,true,false,false,false])

end


@testset "recall" begin

  @test 1 == 1

end


@testset "fscore" begin

  @test 1 == 1

end


@testset "false_positives" begin

  @test 1 == 1

end


end #module ScoresTests
