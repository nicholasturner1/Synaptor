#!/bin/bash

case $1 in
    chunk_ccs)   python3 chunk_ccs.py ${@:2} ;;
    merge_ccs)   python3 merge_ccs.py ${@:2} ;;
    asynet_pass) python3 asynet_pass.py ${@:2} ;;
    merge_edges) python3 merge_edges.py ${@:2} ;;
    remap_ids)   python3 remap_ids.py ${@:2} ;;
    *)  echo "invalid task name"
esac
