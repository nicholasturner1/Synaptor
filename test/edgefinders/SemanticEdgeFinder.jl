module SemanticEFTests


using Base.Test


import ....Synaptor.EdgeFinders.SemanticEF


@testset "Semantic EdgeFinder" begin


@testset "findedges_w_sem" begin

  test_morphseg = [1 0 2];
  test_psdseg   = [1 1 1];

  axon_label = 1
  dend_label = 2

  semmap1 = Dict( 1 => 1, 2 => 2 )
  semmap2 = Dict( 1 => 1, 2 => 1 )
  semmap3 = Dict( 1 => 2, 2 => 1 )

  #Standard test
  es1, inv1, ol1 = SemanticEF.findedges_w_sem(test_psdseg, test_morphseg,
                                              semmap1, axon_label, dend_label)
  @test es1[1] == (1,2)
  @test length(es1) == 1
  @test length(inv1) == 0


  #Invalid edge
  es2, inv2, ol2 = SemanticEF.findedges_w_sem(test_psdseg, test_morphseg,
                                              semmap2, axon_label, dend_label)

  @test inv2[1] == 1
  @test length(es2) == 0
  @test length(inv2) == 1

  #Reversed edge
  es3, inv3, ol3 = SemanticEF.findedges_w_sem(test_psdseg, test_morphseg,
                                              semmap3, axon_label, dend_label)
  @test es3[1] == (2,1)
  @test length(es3) == 1
  @test length(inv3) == 0

end


@testset "_filter_edges" begin

  test_max_ax = Dict( 1 => 1, 2 => 0, 3 => 1, 4 => 5 )
  test_max_de = Dict( 1 => 1, 2 => 1, 3 => 0, 4 => 10)

  valid, invalid = SemanticEF._filter_edges( test_max_ax, test_max_de )

  @test length(valid)   == 2
  @test length(invalid) == 2

  @test 1 in valid
  @test 2 in invalid
  @test 3 in invalid
  @test 4 in valid

end


end #@testset Semantic EdgeFinder

end #module SemanticEFTests
