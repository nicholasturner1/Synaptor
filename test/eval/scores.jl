
module ScoresTests 

using Base.Test

import ....Synaptor.Eval.Scores


@testset "prec_score" begin

  l1 = [1,2,3,4]
  l2 = [2,3,4]
  l3 = [1,1,2,3,4]
  l0 = []

  #basic stuff
  @test Scores.prec_score(l1,l2) == (0.75, Bool[true,false,false,false])
  @test Scores.prec_score(l2,l1) == (1,    Bool[false,false,false])
  @test Scores.prec_score(l1,l0) == (0,    Bool[true,true,true,true])
  @test Scores.prec_score(l0,l1) == (1,    Bool[])

  #duplicates
  @test Scores.prec_score(l3,l1,true)  == (0.8,  Bool[false,true,false,false,false])
  @test Scores.prec_score(l3,l1,false) == (1,    Bool[false,false,false,false])
  @test Scores.prec_score(l3,l2,true)  == (0.6,  Bool[true,true,false,false,false])

end


@testset "rec_score" begin

  l1 = [1,2,3,4]
  l2 = [2,3,4]
  l3 = [1,1,2,3,4]
  l0 = []
  
  @test Scores.rec_score(l1,l2) == (1,    Bool[false,false,false])
  @test Scores.rec_score(l2,l1) == (0.75, Bool[true,false,false,false])
  @test Scores.rec_score(l0,l1) == (0,    Bool[true,true,true,true])

end


@testset "fscore" begin

  @test Scores.fscore( 1, 0, 0, 1  ) == 1
  @test Scores.fscore( 9, 0, 0, 1  ) == 1
  @test Scores.fscore( 1, 0, 0, 10 ) == 1

  @test Scores.fscore( 0, 1, 1, 1  ) == 0
  @test Scores.fscore( 0, 9, 9, 1  ) == 0
  @test Scores.fscore( 0, 1, 1, 10 ) == 0

  @test Scores.fscore( 4, 1, 1, 1  ) == 8 / 10
  @test Scores.fscore( 4, 4, 4, 0.5) == 5 / 10
  @test Scores.fscore( 4, 4, 4, 2  ) == 20/ 40

end


@testset "false_positives" begin

  l1 = [1,2,3,4]
  l2 = [2,3,4]
  l3 = [1,1,2,3,4]
  lt1 = [(1,),(2,),(3,),(4,)]
  lt2 = [(2,),(3,),(4,)]
  l0 = []

  @test Scores.false_positives(l1,l2)   == [true,false,false,false]
  @test Scores.false_positives(l2,l1)   == [false,false,false]
  @test Scores.false_positives(lt1,lt2) == [true,false,false,false]
  @test Scores.false_positives(lt2,lt1) == [false,false,false]
 
  @test Scores.false_positives(lt1,l1)  == [true,true,true,true] 
  @test Scores.false_positives(l1,l0)   == [true,true,true,true]

end


end #module ScoresTests
