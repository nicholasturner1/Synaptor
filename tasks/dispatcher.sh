#!/bin/bash

case $1 in
    chunk_ccs)        python3 chunk_ccs.py ${@:2} ;;
    merge_ccs)        python3 merge_ccs.py ${@:2} ;;
    chunk_edges)      python3 chunk_edges.py ${@:2} ;;
    merge_edges)      python3 merge_edges.py ${@:2} ;;
    remap_ids)        python3 remap_ids.py ${@:2} ;;
    chunk_overlaps)   python3 chunk_overlaps.py ${@:2} ;;
    merge_overlaps)   python3 merge_overlaps.py ${@:2} ;;
    *)  echo "invalid task name $1"
esac
