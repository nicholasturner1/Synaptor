#!/usr/bin/env python3

#At the moment - I'm going to do this in the dumbest way possible
# will revisit this once the other stuff is complete
import subprocess


def send_local_file(local_name, remote_name):
    subprocess.check_output(["gsutil", "cp", local_name, remote_name])


def send_local_files(local_names, remote_dir):
    subprocess.check_output(["gsutil", "cp", "-m", *local_names, remote_dir])
