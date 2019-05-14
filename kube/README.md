# Kubernetes Framework

A user can run distributed workflows on a kubernetes cluster using the scripts in this directory. First, the user will need to set up a cluster and deploy one of the deployment files here depending on their requirements (CPU nodes, GPU nodes, or a mix of both), along with the required secret files. Next, the user will need to allow their pods to access some shared file storage system (e.g. Google Cloud Storage or Amazon S3), and set up a task queue (see [seunglab/python-task-queue](https://github.com/seung-lab/python-task-queue)). The user will also currently need to set up a database that each pod can access. Once this infrastructure is in place, an outline for the remaining steps is below.

## Creating a configuation file

`synaptor.cfg` represents a template configuration file which records all of the required info for your pods to know how to process a dataset. Extra information about each field is below.

### Volumes

Each volume is a path to a volumetric dataset in Neuroglancer Precomputed / CloudVolume format. 
* `descriptor` - the voxelwise descriptor for your application (e.g. voxelwise synaptic cleft or organelle predictions)
* `output` - location of the output segmentation of this descriptor
* `temp_output` - an extra volume for chunked segmentation output. This is often useful in the case of any user error during the workflow. It can be removed upon workflow completion, and the bold can also set this to the same path as `output`

### Dimensions

* `voxelres` - size of each voxel in arbitrary units (often nanometers)
* `startcoord` - starting voxel coordinate (inclusive) of the bounding box within the descriptor volume that you wish to process
* `vol_shape` - the size of the processing volume in voxels, the full bounding box can be represented by (`startcoord + vol_shape`)
* `chunk_shape` - the shape of chunk each chunkwise process should use in voxels

### Parameters

* `ccthresh` - connected component threshold
* `szthresh` - high pass threshold for segments, can be set to 0 if desired
* `dustthresh` - a high pass threshold for chunkwise segments, can be set to 0 if desired
* `num_merge_tasks` - some steps to merge information across chunks can be parallelized. This specifies how many tasks those steps should use. This should be set to 1 for all but the most intensive workflows.

### Workspaces

* `workspacetype` - Whether a database or file system is used for most of the intermediate data. This is required to be `Database` for now
* `queueurl` - A URL to reach the task queue ([seunglab/python-task-queue](https://github.com/seung-lab/python-task-queue))
* `connectionstr` - A SQLAlchemy connection string to the database. Use the incantation `PROC_FROM_FILE` instead if this is passed to the pod as a secret.
* `storagedir` - A shared file storage system directory to use for intermediate and output data. This is where information files should appear for segment location information (centroids, bounding boxes, sizes), as well as edge lists if computed.

## Running distributed tasks

Once you've completed filling out the configuration fields for your task, all you'll need to do is to run the task generation scripts which describe your workflow. This setup does not handle dependencies, so you'll need to start each wave of tasks manually.  

For each step, pass the configuration file to the `task_generation` script for your desired step. If your queue does not support ordered tasks, you will need to wait until those tasks have been completed before moving on to the next step.  

Some common workflows are listed below. Each step matches a task script in the main repo directory, and you can find a basic descriptions in the documentation there.

* Distributed Connected Components: `init_db` -> `chunk_ccs` -> `match_contins` -> `seg_graph_ccs` -> `chunk_seg_map` -> `merge_seginfo` -> `remap`
* Synapse Segmentation and Assignment: `init_db` -> `chunk_ccs` -> `match_contins` -> `seg_graph_ccs` -> chunk_seg_map` -> `merge_seginfo` -> `chunk_edges` -> `pick_edge` -> `merge_dups` -> `remap`
