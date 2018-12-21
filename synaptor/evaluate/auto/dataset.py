import gc

from ... import io

class EvalDataset(object):

    def __init__(self, *args):

        self.vols = []

        for arg in args:
            if isinstance(arg, EvalDataset):
                self.vols.extend(arg.vols)
            elif isinstance(arg, EvalVol):
                self.vols.append(arg)
            elif isinstance(arg, dict):
                self.vols.append(EvalVol(**arg))
            elif isinstance(arg, list):
                self.vols.extend([EvalVol(**v) for v in arg])
            else:
                raise(ValueError("Unknown argument {}".format(arg)))

    def read(self):
        for vol in self.vols:
            vol.read()

    def read_images(self, reqd=False):
        for vol in self.vols:
            vol.read_images(reqd=reqd)
    def read_segs(self, reqd=False):
        for vol in self.vols:
            vol.read_segs(reqd=reqd)
    def read_labels(self, reqd=True):
        for vol in self.vols:
            vol.read_labels(reqd=reqd)
    def read_preds(self, reqd=True):
        for vol in self.vols:
            vol.read_preds(reqd=reqd)
    def read_masks(self, reqd=False):
        for vol in self.vols:
            vol.read_masks(reqd=reqd)

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
    def masks(self):
        return [vol.mask for vol in self.vols]
    @property
    def to_ignore(self):
        return [vol.to_ignore for vol in self.vols]

    def apply_mask(self):
        for vol in self.vols:
            vol.apply_mask()

    def __len__(self):
        return len(self.vols)


class EvalVol(object):

    def __init__(self,
                 image_fname=None, seg_fname=None,
                 label_fname=None, pred_fname=None,
                 mask_fname=None,
                 to_ignore=[],
                 **attrs):

        self._image = None
        self._seg = None
        self._label = None
        self._pred = None
        self._mask = None
        self.to_ignore = to_ignore

        self._image_fname = image_fname
        self._seg_fname = seg_fname
        self._label_fname = label_fname
        self._pred_fname = pred_fname
        self._mask_fname = mask_fname

        #Can access other attributes by attributes dict,
        # or by attribute name
        self._attributes = attrs
        for (k,v) in attrs.items():
            setattr(self, k, v)

    def read(self):
        self.read_image()
        self.read_seg()
        self.read_label()
        self.read_pred()
        self.read_mask()

    def read_if_not_read(self, fname, value, ftype, reqd=True):
        if value is None:
            if reqd:
                assert fname is not None, "Empty {} name".format(ftype)

            if fname is None: #not reqd if this passes
                return None

            print("Reading {ftype}: {fname}".format(ftype=ftype, fname=fname))
            data = io.read_h5(fname)
            if len(data.shape) == 4:
                assert data.shape[0] == 1, "need a single 3d vol"
                data = data[0,...]
            return data.transpose((2,1,0))
        else:
            return value

    def read_image(self, reqd=False):
        self._image = self.read_if_not_read(self._image_fname,
                                            self._image, "image", reqd=reqd)
    def read_seg(self, reqd=False):
        self._seg = self.read_if_not_read(self._seg_fname,
                                          self._seg, "seg", reqd=reqd)
    def read_label(self, reqd=True):
        self._label = self.read_if_not_read(self._label_fname,
                                            self._label, "label", reqd=reqd)
    def read_pred(self, reqd=True):
        self._pred = self.read_if_not_read(self._pred_fname,
                                           self._pred, "pred", reqd=reqd)
    def read_mask(self, reqd=False):
        self._mask = self.read_if_not_read(self._mask_fname,
                                            self._mask, "mask", reqd=reqd)

    def delete(self):
        self._image = None
        self._seg = None
        self._label = None
        self._pred = None
        self._mask = None
        gc.collect()

    def apply_mask(self):
        if self._mask is not None:
            self._pred[self._mask == 0] = 0
            self._label[self._mask == 0] = 0
        else:
            print("WARNING: Skipping masking for a volume")

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
    @property
    def mask(self):
        return self.return_if_read(self._mask)
