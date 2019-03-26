#!/bin/bash

case $1 in
    chunk_ccs)        python3 chunk_ccs.py ${@:2} ;;
    match_contins)    python3 match_contins.py ${@:2} ;;
    seg_graph_ccs)    python3 seg_graph_ccs.py ${@:2} ;;
    chunk_seg_map)    python3 chunk_seg_map.py ${@:2} ;;
    merge_seginfo)    python3 merge_seginfo.py ${@:2} ;;
    chunk_edges)      python3 chunk_edges.py ${@:2} ;;
    pick_edge)        python3 pick_edge.py ${@:2} ;;
    merge_dups)       python3 merge_dups.py ${@:2} ;;
    remap_ids)        python3 remap_ids.py ${@:2} ;;
    chunk_overlaps)   python3 chunk_overlaps.py ${@:2} ;;
    merge_overlaps)   python3 merge_overlaps.py ${@:2} ;;
    chunk_anchors)    python3 chunk_anchors.py ${@:2} ;;
    create_index)     python3 create_index.py ${@:2} ;;
    *)  echo "invalid task name $1"
esac
