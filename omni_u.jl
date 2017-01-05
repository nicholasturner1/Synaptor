#!/usr/people/nturner/julia/julia

__precompile__()

module omni_u

import io_u
import vol_u
using HDF5

seg_dset_name = "/main";
mst_dset_name = "/dend";
mst_edge_dset_name = "/dendValues";

export read_child_file, reverse_child_mapping, merge_selected_parent_groups
export read_MST, read_ws_seg
#----------------------------
"""

    read_MST( segmentPairs, segmentPairAffinities, threshold )

  Reads in the MST from segmentation files thresholded at the given
  value. Only contains key value pairs for a node if it is not a root node
"""
function read_MST( segmentPairs, segmentPairAffinities, threshold )

  assignment = Dict{Int,Int}();

  for i in eachindex( segmentPairAffinities )

    if segmentPairAffinities[i] > threshold
      child, parent = segmentPairs[i,:];
      # parent, child = segmentPairs[i,:];
      #println("child: $child, parent: $parent, val: $(segmentPairAffinities[i])")
      assignment[ child ] = get( assignment, parent, parent )
    end

  end

  #for k in keys(assignment)
  #  v = assignment[k]
  #  while v != get(assignment,v,v)
  #    println( "$v -> $(assignment[v])")
  #    assignment[k] = assignment[v]
  #  end
  #end

  assignment
end


function import_ws_seg( fname )

  seg         = HDF5.h5read( fname, seg_dset_name )
  segPairs    = HDF5.h5read( fname, mst_dset_name )
  segPairAffs = HDF5.h5read( fname, mst_edge_dset_name )

  seg, segPairs, segPairAffs
end


"""

    read_ws_seg( fname, thresh )
"""
function read_ws_seg( fname, thresh=1 )

  seg, segPair, segPairAffs = import_ws_seg(fname)

  mst_assignment = read_MST( segPairs, segPairAffs, thresh )
  vol_u.relabel_data!( seg, mst_assignment )

  seg
end

"""
    read_child_file( filename )

  Read a descendant file list from omni, return an Array{Array{Int,1},1}
that represents the parent -> child group mapping.
"""
function read_child_file( filename )


  f = open( filename )
  lines = readlines(f);

  parent_to_children = Array( Array{UInt32,1}, (length(lines),) );

  for ln in lines

    fields = split(ln, ": ");

    parent = parse(Int,fields[1]);
    #second field is either a comma-delimited list
    # of child_ids, or "child"
    children_str = fields[2];

    # == string child\n shortcut
    if children_str[1] == 'c'
      children_arr = [];

    else
      children_arr = map(x->parse(UInt32,x), split(children_str,','));
    end

    parent_to_children[ parent ] = children_arr;

  end #for ln

  close(f);

  return parent_to_children;

end

"""
    reverse_child_mapping( parent_to_child_str )

  Take an array of children arrays, and reverse the mapping so
that children point to their parent id.
"""
function reverse_child_mapping( parent_to_children )

  child_to_parent = zeros( UInt32, (length(parent_to_children),) );

  for parent in 1:length(parent_to_children)

    children_arr = parent_to_children[ parent ];

    #if 'parent' node was a child, then this will
    # pass silently
    for child in children_arr
      child_to_parent[child] = parent;
    end #for child

  end #for ln

  return child_to_parent;
end

"""
    write_mapping( filename, mapping_array )

  Write a file describing a mapping for a sanity check.
"""
function write_mapping( filename, mapping_array )

  open( filename, "w+" ) do f
    for (child, parent) in enumerate( mapping_array )

      write(f, "$child: $parent\n")

    end #for
  end #open
end

"""
    merge_selected_parent_groups( parent_to_children, child_to_parent, ids )

  Find a mapping (array) so that segments at the ids are merged to all their
connected ids, and others are left alone.

Assumes children have only one parent
"""
function merge_selected_parent_groups( parent_to_children, child_to_parent, ids )

  @assert length(parent_to_children) == length(child_to_parent);

  #start with each index mapping to itself
  # oooooohhh this is ugly, not sure how else to do this for now
  mapping = Array( UnitRange{UInt32}(1,length(parent_to_children)) );

  for id in ids

    parent = child_to_parent[ id ];

    siblings = parent_to_children[ parent ];

    for sibling in siblings
      mapping[ sibling ] = parent;
    end

  end #for

  return mapping

end
#----------------------------
end #module end
