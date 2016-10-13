# Synaptor
Scripts for filtering convnet output for synapses, and assigning synapse directionality using segmentation and semantic information.

Main executables are:
main.jl - For when both datasets are small and can fit in memory easily
main_ooc.jl - For when either dataset can't fit into memory
create_seg_volume.jl - For creating a segmentation from the results of main_ooc.jl

