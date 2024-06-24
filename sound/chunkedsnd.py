import numpy as np
from pathlib import Path
from contextlib import contextmanager, ExitStack
from darr.basedatadir import DataDir
from darr.metadata import MetaData
from .snd import BaseSnd
from .audiofile import AudioFile, encodingtodtype
from .darrsnd import DarrSnd, SndInfo
from .utils import wraptimeparamsmethod
from .audioimport import list_audiofiles
from ._version import get_versions


__all__ = ['ChunkedSnd', 'audiodir_to_chunkedsnd']


# Are there things shared between disk-based objects that justify a Subclass
# of BaseSnd?

class ChunkedSnd(BaseSnd, SndInfo):
    _classid = 'ChunkedSnd'
    _classdescr = ('represents a continuous sound stored in separate, '
                   'contiguous audio files')
    _suffix = '.chunkedsnd'
    _settableparams = ('fs', 'metadata', 'origintime', 'scalingfactor',
                       'startdatetime', 'unit')
    _dtypes = ('float32', 'float64')
    _defaultdtype = 'float64'
    _sndinfopath = 'sndinfo.json'
    _metadatapath = 'metadata.json'

    def __init__(self, path, accessmode='r', mmap=True):
        chunkedsnddirpath, sndinfopath = self._check_path(path)
        self._chunkedsnddirpath = chunkedsnddirpath
        SndInfo.__init__(self, path=sndinfopath, accessmode=accessmode,
                         settableparams=self._settableparams)
        self._snds = []
        ci = self._sndinfo._read()
        if ci['filetype'] == 'AudioFile':
            SndClass = AudioFile
        else:
            raise TypeError(f"file type '{ci['filetype']}' not understood")
        chunknframes = [0]
        for pathname in ci['chunkpaths']:
            snd = SndClass(chunkedsnddirpath / pathname, mmap=mmap)
            self._snds.append(snd)
            chunknframes.append(snd.nframes)
        self._chunknframes = np.array(chunknframes, dtype='int64')
        self._endindices = np.cumsum(self._chunknframes)
        nframes = self._chunknframes.sum()
        nchannels = ci['nchannels']
        dtype = ci['dtype']
        si = self._sndinfo._read()
        kwargs = {sp: si[sp] for sp in self._settableparams if sp in si}
        if 'fs' in kwargs:
            fs = kwargs.pop('fs')
        if 'dtype' in kwargs:
            dtype = kwargs.pop('dtype')
        else:
            dtype = self._defaultdtype
        BaseSnd.__init__(self, nframes=nframes, nchannels=nchannels, fs=ci['fs'],
                         sampledtype=dtype,
                         setparamcallback=self._set_parameter, **kwargs)
    @property
    def chunkedsnddirpath(self):
        return self._chunkedsnddirpath
    def _check_path(self, path):
        path = Path(path)
        sndinfopath = path / self._sndinfopath
        if not path.exists():
            raise IOError(f"ChunkedSnd path {path} does not exist")
        if not sndinfopath.exists():
            raise IOError(f"Path {path} exist, but contains no file "
                          f"{self._sndinfopath}. This is not a valid ChunkedSnd "
                          f"folder.")

        return path, sndinfopath

    @contextmanager
    def open(self):
        with ExitStack() as stack:
            ahs = [stack.enter_context(s.open()) for s in self._snds]
            yield None

    @wraptimeparamsmethod
    def read_frames(self, startframe=None, endframe=None, starttime=None,
                    endtime=None, startdatetime=None, enddatetime=None,
                    channelindex=None, out=None, dtype='float64'):
        dtype = self._check_dtype(dtype)
        frames = np.empty((endframe - startframe, self._nchannels), dtype)
        startchunk, endchunk = np.searchsorted(self._endindices, (startframe, endframe), side="right") - (1, 1)
        startframe -= self._endindices[startchunk]
        endframe -= self._endindices[endchunk]
        if startchunk == endchunk:
            frames[:] = self._snds[startchunk].read_frames(
                startframe=startframe, endframe=endframe, dtype=dtype)
        else:
            ar = self._snds[startchunk].read_frames(startframe=startframe,
                                                    dtype=dtype)
            frames[:len(ar)] = ar
            nfilled = len(ar)
            for snd in self._snds[startchunk + 1:endchunk]:
                ar = snd.read_frames(dtype=dtype)
                frames[nfilled:nfilled + len(ar)] = ar
                nfilled += len(ar)
            if endframe != 0:
                ar = self._snds[endchunk].read_frames(endframe=endframe,
                                                      dtype=dtype)
                frames[nfilled:nfilled + len(ar)] = ar
        if channelindex is not None:
            frames = frames[:,channelindex]
        return frames

def audiodir_to_chunkedsnd(path, extension='.wav', origintime=0.0,
                           startdatetime='NaT', metadata=None, dtype=None,
                           overwrite=False):
    path = Path(path)
    sndinfo = list_audiofiles(path, extensions=(extension,), recursive=False)
    #FIXME assert same sound types
    subtype = sndinfo['audioencoding'][0]
    if dtype is None:
        dtype = ChunkedSnd._defaultdtype
    dtype = BaseSnd._check_dtype(BaseSnd, dtype)
    startdatetime = np.datetime64(startdatetime)
    d = {'filetype': 'AudioFile',
         'chunkpaths': [p.name for p in sndinfo['paths']],
         'fs': sndinfo['fs'][0],
         'audiofileformat': sndinfo['audiofileformat'][0],
         'audioencoding': sndinfo['audioencoding'][0],
         'endiannes': sndinfo['endianness'][0],
         'dtype': dtype,
         'nchannels': sndinfo['nchannels'][0],
         'origintime': origintime,
         'startdatetime': str(startdatetime)}
    bd = DataDir(path)
    bd._write_jsondict(path / ChunkedSnd._sndinfopath, d=d,
                       overwrite=overwrite)
    if metadata is not None:
        bd._write_jsondict(ChunkedSnd._metadatapath, d=dict(metadata),
                           overwrite=overwrite)
    return ChunkedSnd(path)







