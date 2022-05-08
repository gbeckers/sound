import numpy as np
from pathlib import Path
from darr import asarray, create_array, Array, \
    delete_array
from darr.numtype import numtypesdescr

from .snd import BaseSnd
from .sndinfo import SndInfo, _create_sndinfo
from .utils import wraptimeparamsmethod
from ._version import get_versions

__all__ = ['available_darrsndformats', 'create_darrsnd', 'DarrSnd']

available_darrsndformats = dict(numtypesdescr)


# FIXME should this have a subformattype attribute?
class DarrSnd(BaseSnd, SndInfo):

    """

    Notes
    -----
    Does not have a scaling factor since it is easy just to use a float
    format so that any scaling could have been applied when the DarrSnd was
    created. This is much more efficient.

    """

    _framespath = 'frames.darr'
    _classid = "DarrSnd"
    _suffix = '.snd'
    _fileformat = 'darrsnd'
    _settableparams = ('fs', 'metadata', 'origintime', 'scalingfactor',
                       'startdateime', 'unit')

    def __init__(self, path, accessmode='r'):
        SndInfo.__init__(self, path=path, accessmode=accessmode)
        path = Path(path)
        self._frames = frames = Array(path=path / self._framespath, accessmode=accessmode)
        if frames.ndim != 2:
            raise ValueError(f"`Darr Array` has to have 2 dimensions (now: {frames.ndim})")
        nframes, nchannels = frames.shape
        si = self.sndinfo
        BaseSnd.__init__(self, nframes=nframes, nchannels=nchannels,
                         fs=si['fs'], dtype=frames.dtype,
                         startdatetime=si['startdatetime'],
                         origintime=si['origintime'], metadata=self.metadata,
                         scalingfactor=None, unit=si['unit'],
                         setparamcallback=self._set_parameter)

        self.open = self._frames.open

    @property
    def fileformat(self):
        return self._fileformat

    @property
    def fileformatsubtype(self):
        return self._frames._arrayinfo['numtype']

    @property
    def endianness(self):
        return self._frames._arrayinfo['byteorder']

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
    sndpath = Path(path)
    if sndpath.suffix not in (SndInfo._suffix, SndInfo._suffix.upper()):
        sndpath = path.with_suffix(SndInfo._suffix)
    darrpath = sndpath.with_suffix('.darr')

    shape = (nframes, nchannels)
    create_array(path=darrpath, shape=shape,
                 dtype=dtype, fill=fill, fillfunc=fillfunc,
                 accessmode=accessmode,
                 chunklen=chunksize, metadata=None, overwrite=overwrite)
    bsnd = BaseSnd(nframes=nframes, nchannels=nchannels, fs=fs, dtype=dtype,
                   startdatetime=startdatetime, origintime=origintime,
                   unit=unit, metadata=metadata)
    d = bsnd._saveparams()
    _create_sndinfo(sndpath, d=d, overwrite=overwrite)
    return DarrSnd(sndpath, accessmode=accessmode)

