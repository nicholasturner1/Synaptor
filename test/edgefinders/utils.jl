
module UtilsTests

using Base.Test

import ....Synaptor.EdgeFinders.Utils


@testset "sum_overlap_weight" begin

  seg1 = [1 1; 0 0]
  seg2 = [0 1; 0 1]
  seg3 = [1 0; 1 0]
  seg4 = [0 0; 1 1]

  w1 = [1 2; 3 4]
  w2 = [4 3; 2 1]
  w3 = [0 0; 0 0]

  @test Utils.sum_overlap_weight(seg1,seg2,w1)[1,1] == 2
  @test Utils.sum_overlap_weight(seg1,seg3,w1)[1,1] == 1
  @test Utils.sum_overlap_weight(seg1,seg4,w1)[1,1] == 0

  @test Utils.sum_overlap_weight(seg2,seg3,w1)[1,1] == 0
  @test Utils.sum_overlap_weight(seg2,seg4,w1)[1,1] == 4

  @test Utils.sum_overlap_weight(seg3,seg4,w1)[1,1] == 3


  @test Utils.sum_overlap_weight(seg1,seg2,w2)[1,1] == 3
  @test Utils.sum_overlap_weight(seg1,seg3,w2)[1,1] == 4
  @test Utils.sum_overlap_weight(seg1,seg4,w2)[1,1] == 0

  @test Utils.sum_overlap_weight(seg2,seg3,w2)[1,1] == 0
  @test Utils.sum_overlap_weight(seg2,seg4,w2)[1,1] == 1

  @test Utils.sum_overlap_weight(seg3,seg4,w2)[1,1] == 2


  @test Utils.sum_overlap_weight(seg1,seg2,w3)[1,1] == 0
  @test Utils.sum_overlap_weight(seg1,seg3,w3)[1,1] == 0
  @test Utils.sum_overlap_weight(seg1,seg4,w3)[1,1] == 0

  @test Utils.sum_overlap_weight(seg2,seg3,w3)[1,1] == 0
  @test Utils.sum_overlap_weight(seg2,seg4,w3)[1,1] == 0

  @test Utils.sum_overlap_weight(seg3,seg4,w3)[1,1] == 0
end


@testset "count_overlapping_labels" begin

  seg1 = [1 2; 3 4]
  seg2 = [5 5; 5 5]
  seg3 = [0 0; 0 0]

  res1 = Utils.count_overlapping_labels(seg1,seg2)
  for i in 1:4
    @test res1[i,5] == 1
  end

  @test size(Utils.count_overlapping_labels(seg1,seg3)) == (4,0)
  @test size(Utils.count_overlapping_labels(seg1,seg3,5)) == (5,5)

end


@testset "find_max_overlaps" begin

  om1 = sparse([ 1 2; 0 0; 3 0 ])

  maxs, inds = Utils.find_max_overlaps(om1)

  @test maxs[1] == 2
  @test inds[1] == 2

  @test maxs[2] == 0
  @test inds[2] == 0

  @test maxs[3] == 3
  @test inds[3] == 1

  maxs, inds = Utils.find_max_overlaps(om1, [5,10,15])

  @test maxs[1] == 2
  @test inds[1] == 10
  @test inds[2] == 0
  @test inds[3] == 5

  maxs, inds = Utils.find_max_overlaps(om1, [1,2,3], [5,10,15])

  @test maxs[5] == 2
  @test inds[5] == 2
  @test maxs[10] == 0
  @test inds[10] == 0
  @test maxs[15] == 3
  @test inds[15] == 1

end

end #module UtilsTests
