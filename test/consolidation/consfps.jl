module ConsolidateFocalPointsTests

using ....Synaptor.Consolidation.ConsolidateFocalPoints

using Base.Test

@testset "consolidate_focal_points" begin

set1 = Dict( 1 => ((-1,-1,-1),(1,1,1)),
             2 => ((2,2,2),(3,3,3)) )
set2 = Dict( 1 => ((4,4,4),(-1,-1,-1)),
             2 => ((2,2,2),(3,3,3)),
             3 => ((5,5,5),(6,6,6)) )

res = ConsolidateFocalPoints.consolidate_focal_points([set1,set2])

@test res[1] == ((4,4,4),(1,1,1))
@test res[2] == ((2,2,2),(3,3,3))
@test res[3] == ((5,5,5),(6,6,6))

end #testset consolidate_focal_points

end #module ConsolidateFocalPointsTests
