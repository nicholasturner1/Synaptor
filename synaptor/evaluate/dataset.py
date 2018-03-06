import gc

from .. import io

class EvalDataset(object):

    def __init__(self, *args):

        self.vols = []

        for arg in args:
            if isinstance(arg, EvalDataset):
                self.vols.extend(arg.vols)
            elif isinstance(arg, EvalDataVol):
                self.vols.append(arg)
            elif isinstance(arg, dict):
                self.vols.append(EvalDataVol(**arg))
            elif isinstance(arg, list):
                self.vols.extend([EvalDataVol(**v) for v in arg])
            else:
                raise(ValueError("Unknown argument {}".format(arg)))

    def read(self):
        for vol in self.vols:
            vol.read()

    def delete(self):
        for vol in self.vols:
            vol.delete()

    @property
    def images(self):
        return [vol.image for vol in self.vols]

    @property
    def segs(self):
        return [vol.seg for vol in self.vols]

    @property
    def labels(self):
        return [vol.label for vol in self.vols]

    @property
    def preds(self):
        return [vol.pred for vol in self.vols]

    @property
    def to_ignore(self):
        return [vol.to_ignore for vol in self.vols]

    def __len__(self):
        return len(self.vols)


class EvalDataVol(object):

    def __init__(self, image_fname, seg_fname, 
                 label_fname, pred_fname, to_ignore=[], 
                 **kwargs):

        self._image = None
        self._seg = None
        self._label = None
        self._pred = None
        self.to_ignore = to_ignore
        
        self._image_fname = image_fname
        self._seg_fname = seg_fname
        self._label_fname = label_fname
        self._pred_fname = pred_fname

        for (k,v) in kwargs.items():
            setattr(self, k, v)

    def read(self):
        
        self._image = self.read_if_not_read(self._image_fname, 
                                            self._image, "image")
        self._seg = self.read_if_not_read(self._seg_fname, 
                                            self._seg, "seg")
        self._label = self.read_if_not_read(self._label_fname, 
                                            self._label, "label")
        self._pred = self.read_if_not_read(self._pred_fname, 
                                            self._pred, "pred")

    def read_if_not_read(self, fname, value, ftype):
        if value is None:
            print("Reading {ftype}: {fname}".format(ftype=ftype, fname=fname))
            return io.read_h5(fname).transpose((2,1,0))
        else:
            return value

    def delete(self):
        self._image = None
        self._seg = None
        self._label = None
        self._pred = None
        gc.collect()

    def return_if_read(self, value):
        if value is not None:
            return value
        else:
            raise(Exception("Value not read"))

    @property
    def image(self):
        return self.return_if_read(self._image)

    @property
    def seg(self):
        return self.return_if_read(self._seg)

    @property
    def label(self):
        return self.return_if_read(self._label)

    @property
    def pred(self):
        return self.return_if_read(self._pred)
