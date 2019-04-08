import copy
import math
import os
import subprocess

from time import strftime

from cloudvolume import CloudVolume
from cloudvolume.lib import Bbox, Vec, xyzrange, min2, yellow
from taskqueue import GreenTaskQueue

from tasks import SynaptorTask

try:
  OPERATOR_CONTACT = subprocess.check_output("git config user.email", shell=True)
  OPERATOR_CONTACT = str(OPERATOR_CONTACT.rstrip())
except:
  try:
    print(yellow('Unable to determine provenance contact email. Set "git config user.email". Using unix $USER instead.'))
    OPERATOR_CONTACT = os.environ['USER']
  except:
    print(yellow('$USER was not set. The "owner" field of the provenance file will be blank.'))
    OPERATOR_CONTACT = ''

def tup2str(t): 
  return " ".join(map(str, t))

def create_connected_component_tasks(
    outpath, cleftpath, proc_url, proc_dir,
    cc_thresh, sz_thresh, bounds, shape, 
    mip=0, parallel=1, hashmax=1
  ):
  
  shape = Vec(*shape)
  mip = int(mip)

  vol = CloudVolume(cleftpath, mip=mip)
  bounds = vol.bbox_to_mip(bounds, mip=0, to_mip=mip)
  bounds = Bbox.clamp(bounds, vol.bounds)
  
  class ConnectedComponentsTaskIterator(object):
    def __init__(self, level_start, level_end):
      self.level_start = level_start
      self.level_end = level_end
    def __len__(self):
      return self.level_end - self.level_start
    def __getitem__(self, slc):
      itr = copy.deepcopy(self)
      itr.level_start = self.level_start + slc.start 
      itr.level_end = self.level_start + slc.stop
      return itr
    def __iter__(self):
      self.bounds = bounds.clone()
      self.bounds.minpt.z = bounds.minpt.z + self.level_start * shape.z
      self.bounds.maxpt.z = bounds.minpt.z + self.level_end * shape.z

      for startpt in xyzrange( self.bounds.minpt, self.bounds.maxpt, shape ):
        task_shape = min2(shape.clone(), self.bounds.maxpt - startpt)

        task_bounds = Bbox( startpt, startpt + task_shape )
        if task_bounds.volume() < 1:
          continue

        chunk_begin = tup2str(task_bounds.minpt)
        chunk_end = tup2str(task_bounds.maxpt)

        cmd = f"""
          chunk_ccs {outpath} {cleftpath} {proc_url} \
            {cc_thresh} {sz_thresh} \
            --chunk_begin {chunk_begin} --chunk_end {chunk_end} --mip {mip} \
            --proc_dir {proc_dir} --hashmax {hashmax} \
            --parallel {parallel} 
          """.strip()

        yield SynaptorTask(cmd)

      job_details = {
        'method': {
          'task': 'ConnectedComponentsTask',
          'outpath': outpath,
          'cleftpath': cleftpath,
          'proc_url': proc_url,
          'proc_dir': proc_dir,
          'cc_thresh': cc_thresh,
          'sz_thresh': sz_thresh,
          'parallel': parallel,
          'hashmax': hashmax,
          'shape': list(map(int, shape)),
          'bounds': [
            bounds.minpt.tolist(),
            bounds.maxpt.tolist()
          ],
          'mip': mip,
        },
        'by': OPERATOR_CONTACT,
        'date': strftime('%Y-%m-%d %H:%M %Z'),
      }

      dvol = CloudVolume(outpath)
      dvol.provenance.sources = [ cleftpath ]
      dvol.provenance.processing.append(job_details) 
      dvol.commit_provenance()
  
  level_end = int(math.ceil(bounds.size3().z / shape.z)) + 1
  return ConnectedComponentsTaskIterator(0, level_end)

