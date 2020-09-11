import numpy as np
from pathlib import Path
from darr import asarray, create_array, Array, \
    delete_array
from darr.numtype import numtypesdescr

from .snd import BaseSnd
from .disksnd import DataDir, create_datadir
from .utils import wraptimeparamsmethod
from ._version import get_versions

__all__ = ['available_darrsndformats', 'create_darrsnd', 'DarrSnd']

available_darrsndformats = dict(numtypesdescr)


# append?
class DarrSnd(BaseSnd):

    """

    Notes
    -----
    Does not have a scaling factor since it is easy just to use a float
    format so that any scaling could have been applied when the DarrSnd was
    created. This is much more efficient.

    """

    _framespath = 'frames'
    _classid = "DarrSnd"
    _version = get_versions()['version']

    def __init__(self, path, accessmode='r'):
        self._datadir = dd = DataDir(path=path, accessmode=accessmode)
        path = Path(path)
        self._frames = frames = Array(path=path / self._framespath, accessmode=accessmode)
        if frames.ndim != 2:
            raise ValueError(f"`Darr Array` has to have 2 dimensions (now: {frames.ndim})")
        nframes, nchannels = frames.shape
        sndinfo = dd.read_sndinfo()
        BaseSnd.__init__(self, nframes=nframes, nchannels=nchannels,
                         fs=sndinfo['fs'], dtype=frames.dtype,
                         startdatetime=sndinfo['startdatetime'],
                         origintime=sndinfo['origintime'], metadata=dd.metadata,
                         scalingfactor=None, unit=sndinfo['unit'])

        self.open = self._frames.open

    @property
    def datadir(self):
        """Datadir object with useful properties and methods for file/data IO"""
        return self._datadir

    def __str__(self):
        return f'{super().__str__()[:-1]}, {self.dtype}>'

    __repr__ = __str__

    @wraptimeparamsmethod
    def read_frames(self, startframe=None, endframe=None, starttime=None,
                    endtime=None, startdatetime=None, enddatetime=None,
                    channelindex=None, dtype=None, order='K', ndmin=2,
                    normalizeinttoaudiofloat=False):
        if channelindex is None:
            channelindex = slice(None, None, None)
        frames = self._frames[slice(startframe, endframe), channelindex]
        if normalizeinttoaudiofloat:  # 'int32', 'int16'
            if frames.dtype == np.int32:
                frames *= 1 / 0x80000000
            elif frames.dtype == np.int16:
                frames *= 1 / 0x8000
            else:
                raise TypeError(f"'normalizeinttoaudiofloat' parameter is "
                                f"True, but can only applied to int16 and "
                                f"int32 data; received {frames.dtype} "
                                f"data.")
        return np.array(frames, copy=False, dtype=dtype, order=order,
                        ndmin=ndmin)


def create_darrsnd(path, nframes, nchannels, fs, startdatetime='NaT',
                   origintime=0.0, dtype='float32', fill=None, fillfunc=None,
                   accessmode='r+', chunksize=1024 * 1024, metadata=None,
                   unit=None, overwrite=False):
    path = Path(path)
    if path.suffix != 'darrsnd':
        path = path.with_suffix('.darrsnd')
    dd = create_datadir(path=path, overwrite=overwrite)
    shape = (nframes, nchannels)
    framespath = path / DarrSnd._framespath
    da = create_array(path=framespath, shape=shape,
                   dtype=dtype, fill=fill, fillfunc=fillfunc,
                   accessmode=accessmode,
                   chunklen=chunksize, metadata=None, overwrite=overwrite)
    bsnd = BaseSnd(nframes=nframes, nchannels=nchannels, fs=fs, dtype=dtype,
                   startdatetime=startdatetime, origintime=origintime,
                   unit=unit, metadata=metadata)

    sndinfo = bsnd._saveparams()
    dd.write_sndinfo(sndinfo, overwrite=overwrite)
    if (metadata is not None) and (not overwrite):
        dd.metadata.update(bsnd.metadata)
    return DarrSnd(path=path, accessmode=accessmode)

