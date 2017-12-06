#!/usr/bin/env python3
__doc__ = "Quick script to do the necessary setup for a cloud task"

import synaptor as s


def main(proc_dir_path,
         network_fname, net_chkpt_fname,
         cv_path, cv_res, cv_size, cv_offset,
         cv_desc, cv_owners):

    print("Uploading network files")
    s.edges.io.upload_network(network_fname, net_chkpt_fname, proc_dir_path)

    print("Creating CloudVolume")
    s.io.create_seg_volume(cv_path, cv_res, cv_size,
                           cv_desc, cv_owners,
                           offset=cv_offset)

    print("Setup Complete")


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("proc_dir_path",
                        help="Path to the processing directory")
    parser.add_argument("network_fname")
    parser.add_argument("net_chkpt_fname")
    parser.add_argument("cv_path",
                        help="Remote path to CloudVolume")
    parser.add_argument("cv_desc",
                        help="CloudVolume provenance description field")
    parser.add_argument("--cv_owners",
                        help="CloudVolume provenance owners field",
                        nargs="+", default=["nturner@cs.princeton.edu"])
    parser.add_argument("--cv_size", nargs="+", default=(69632, 32768, 1792),
                        help="CloudVolume size")
    parser.add_argument("--cv_offset", nargs="+", default=(14336, 12288, 16384),
                        help="CloudVolume offset")
    parser.add_argument("--cv_res", nargs="+", default=(5,5,45),
                        help="CloudVolume voxel resolution")

    args = parser.parse_args()

    main(**vars(args))
