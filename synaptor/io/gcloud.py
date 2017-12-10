#!/usr/bin/env python3

#I'm going to do this in the dumbest way possible
# will revisit this if necessary
#
#Also the aws and gcloud modules are copies at this point, though
# I'm keeping them separate in case I do something fancier later
import os, subprocess

from . import local


def check_slash(path):
    if path[-1] == "/":
        return path
    else:
        return path + "/"


def check_no_slash(path):
    if path[-1] == "/":
        return path[:-1]
    else:
        return path


def send_local_file(local_name, remote_name):
    print(["gsutil", "cp", local_name, remote_name])
    subprocess.check_call(["gsutil", "cp", local_name, remote_name])


def send_local_dir(local_dir, remote_dir):
    print(["gsutil","-m","cp","-r", 
           check_no_slash(local_dir), 
           check_slash(remote_dir)])
    subprocess.check_call(["gsutil","-m","cp","-r", 
                           check_no_slash(local_dir), 
                           check_slash(remote_dir)])


def pull_file(remote_path):
    print(["gsutil","cp",remote_path,"."])
    subprocess.check_call(["gsutil","cp",remote_path,"."])
    return local.pull_file(os.path.basename(remote_path))
    

def pull_all_files(remote_dir):
    print(["gsutil","-m","cp","-r",
           check_no_slash(remote_dir),
           "."])
    subprocess.check_call(["gsutil","-m","cp","-r",
                           check_no_slash(remote_dir),
                           "."])
    return local.pull_all_files(os.path.basename(remote_dir))

