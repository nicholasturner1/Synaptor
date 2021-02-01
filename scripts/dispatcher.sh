#!/bin/bash

case $1 in
    chunk_ccs)        python3 -u chunk_ccs.py ${@:2} ;;
    merge_ccs)        python3 -u merge_ccs.py ${@:2} ;;
    match_contins)    python3 -u match_contins.py ${@:2} ;;
    seg_graph_ccs)    python3 -u seg_graph_ccs.py ${@:2} ;;
    chunk_seg_map)    python3 -u chunk_seg_map.py ${@:2} ;;
    merge_seginfo)    python3 -u merge_seginfo.py ${@:2} ;;
    chunk_edges)      python3 -u chunk_edges.py ${@:2} ;;
    pick_edge)        python3 -u pick_edge.py ${@:2} ;;
    merge_dups)       python3 -u merge_dups.py ${@:2} ;;
    remap_ids)        python3 -u remap_ids.py ${@:2} ;;
    chunk_overlaps)   python3 -u chunk_overlaps.py ${@:2} ;;
    merge_overlaps)   python3 -u merge_overlaps.py ${@:2} ;;
    chunk_anchors)    python3 -u chunk_anchors.py ${@:2} ;;
    create_index)     python3 -u create_index.py ${@:2} ;;
    dedup_chunk_segs) python3 -u dedup_chunk_segs.py ${@:2} ;;
    init_db)          python3 -u init_db.py ${@:2} ;;
    hello_world)      python3 -u hello_world.py ${@:2} ;;
    *)  echo "invalid task name $1"
esac
