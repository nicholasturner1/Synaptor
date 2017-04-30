
module OverlapTests

using Base.Test

import ....Synaptor.SegUtils.Overlap


@testset "Overlap" begin


@testset "sum_overlap_weight" begin

  seg1 = [1 1; 0 0]
  seg2 = [0 1; 0 1]
  seg3 = [1 0; 1 0]
  seg4 = [0 0; 1 1]

  w1 = [1 2; 3 4]
  w2 = [4 3; 2 1]
  w3 = [0 0; 0 0]

  @test Overlap.sum_overlap_weight(seg1,seg2,w1)[1,1] == 2
  @test Overlap.sum_overlap_weight(seg1,seg3,w1)[1,1] == 1
  @test Overlap.sum_overlap_weight(seg1,seg4,w1)[1,1] == 0

  @test Overlap.sum_overlap_weight(seg2,seg3,w1)[1,1] == 0
  @test Overlap.sum_overlap_weight(seg2,seg4,w1)[1,1] == 4

  @test Overlap.sum_overlap_weight(seg3,seg4,w1)[1,1] == 3


  @test Overlap.sum_overlap_weight(seg1,seg2,w2)[1,1] == 3
  @test Overlap.sum_overlap_weight(seg1,seg3,w2)[1,1] == 4
  @test Overlap.sum_overlap_weight(seg1,seg4,w2)[1,1] == 0

  @test Overlap.sum_overlap_weight(seg2,seg3,w2)[1,1] == 0
  @test Overlap.sum_overlap_weight(seg2,seg4,w2)[1,1] == 1

  @test Overlap.sum_overlap_weight(seg3,seg4,w2)[1,1] == 2


  @test Overlap.sum_overlap_weight(seg1,seg2,w3)[1,1] == 0
  @test Overlap.sum_overlap_weight(seg1,seg3,w3)[1,1] == 0
  @test Overlap.sum_overlap_weight(seg1,seg4,w3)[1,1] == 0

  @test Overlap.sum_overlap_weight(seg2,seg3,w3)[1,1] == 0
  @test Overlap.sum_overlap_weight(seg2,seg4,w3)[1,1] == 0

  @test Overlap.sum_overlap_weight(seg3,seg4,w3)[1,1] == 0
end


@testset "count_overlapping_labels" begin

  seg1 = [1 2; 3 4]
  seg2 = [5 5; 5 5]
  seg3 = [0 0; 0 0]

  res1 = Overlap.count_overlapping_labels(seg1,seg2)
  for i in 1:4
    @test res1[i,5] == 1
  end

  @test size(Overlap.count_overlapping_labels(seg1,seg3)) == (4,0)
  @test size(Overlap.count_overlapping_labels(seg1,seg3,5)) == (5,5)

end


@testset "find_max_overlaps" begin

  om1 = sparse([ 1 2; 0 0; 3 0 ])

  maxs, inds = Overlap.find_max_overlaps(om1)

  @test maxs[1] == 2
  @test inds[1] == 2

  @test maxs[2] == 0
  @test inds[2] == 0

  @test maxs[3] == 3
  @test inds[3] == 1

  maxs, inds = Overlap.find_max_overlaps(om1, [5,10,15])

  @test maxs[1] == 2
  @test inds[1] == 10
  @test inds[2] == 0
  @test inds[3] == 5

  maxs, inds = Overlap.find_max_overlaps(om1, [1,2,3], [5,10,15])

  @test maxs[5] == 2
  @test inds[5] == 2
  @test maxs[10] == 0
  @test inds[10] == 0
  @test maxs[15] == 3
  @test inds[15] == 1

end


@testset "find_focal_points" begin

  ccs1 = ones(Int,(3,3,3));
  ccs0 = zeros(Int,(3,3,3));

  seg1 = ones(Int,(3,3,3));
  seg1[:,:,3] = 2;

  edges1 = Dict( 1 => (1,2), 2 => (0,0) )
  edges2 = Dict( 1 => (1,3), 2 => (0,0) )

  fps = Overlap.find_focal_points(ccs1,seg1,edges1)

  @test fps[1][1][3] in (1,2)
  @test fps[1][2][3] == 3
  @test fps[2] == ((-1,-1,-1),(-1,-1,-1))

  fps = Overlap.find_focal_points(ccs0,seg1,edges1)

  @test fps[1] == ((-1,-1,-1),(-1,-1,-1))
  @test fps[2] == ((-1,-1,-1),(-1,-1,-1))

  fps = Overlap.find_focal_points(ccs1,seg1,edges2)

  @test fps[1][1][3] in (1,2)
  @test fps[1][2] == (-1,-1,-1)
  @test fps[2] == ((-1,-1,-1),(-1,-1,-1))

end

end #@testset Overlap


end #module UtilsTests
