import numpy as np
from contextlib import contextmanager
from darr.basedatadir import BaseDataDir
from darr.metadata import MetaData
from .snd import BaseSnd
from .audiofile import AudioFile, encodingtodtype
from .darrsnd import DarrSnd, DataDir
from .utils import wraptimeparamsmethod
from .audioimport import list_audiofiles
from ._version import get_versions

__all__ = ['ChunkedSnd', 'audiodir_to_chunkedsnd']


class ChunkedSnd(BaseSnd):
    _classid = 'ChunkedSnd'
    _classdescr = 'represents a continuous sound stored in separate files'
    _version = get_versions()['version']

    _chunkinfopath = 'chunkinfo.json'
    _metadatapath = 'metadata.json'

    def __init__(self, path, dtype=None, accessmode='r'):
        self._datadir = dd = DataDir(path=path, accessmode=accessmode)
        self._snds = []
        chunknframes = [0]
        ci = dd._read_jsondict(self._chunkinfopath)
        if ci['filetype'] == 'AudioFile':
            SndClass = AudioFile
        elif ci['filetype'] == 'DarrSnd':
            SndClass = DarrSnd
        else:
            raise TypeError(f"file type '{ci['filetype']}' not understood")
        for pn in ci['chunkpaths']:
            snd = SndClass(dd.path / pn, dtype=dtype)
            self._snds.append(snd)
            chunknframes.append(snd.nframes)
        self._chunknframes = np.array(chunknframes, dtype='int64')
        self._endindices = np.cumsum(self._chunknframes)
        nframes = self._chunknframes.sum()
        nchannels = ci['nchannels']
        metadata = MetaData(dd.path / self._metadatapath)
        if dtype is None:
            dtype = ci['dtype']
        BaseSnd.__init__(self, nframes=nframes, nchannels=nchannels, fs=ci['fs'],
                         dtype=dtype,
                         startdatetime=ci['startdatetime'],
                         origintime=ci['origintime'], metadata=metadata,
                         encoding=ci['fileformatsubtype'])

    @property
    def datadir(self):
        """Datadir object with useful properties and methods for file/data IO"""
        return self._datadir

    @contextmanager
    def open(self):
        yield None # still to be implemented

    @wraptimeparamsmethod
    def read_frames(self, startframe=None, endframe=None, starttime=None,
                endtime=None, startdatetime=None, enddatetime=None,
                channelindex=None, dtype=None, normalizeinttoaudiofloat=False):
        if dtype is None:
            dtype = self._dtype
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

def audiodir_to_chunkedsnd(path, extension='.wav', origintime=0.0, startdatetime='NaT', metadata=None,
                           dtype=None, overwrite=False):
    fullpaths, paths, fss, nchannelss, sizes, formats, subtypes, endians = \
        list_audiofiles(path, extensions=(extension,), assertsametype=True)
    subtype = subtypes[0]
    if dtype is None:
        dtype = encodingtodtype.get(subtype, 'float64')
    startdatetime = np.datetime64(startdatetime)
    d = {'filetype': 'AudioFile',
         'chunkpaths': paths,
         'fs': fss[0],
         'fileformat': formats[0],
         'fileformatsubtype': subtypes[0],
         'endiannes': endians[0],
         'dtype': dtype,
         'nchannels': nchannelss[0],
         'origintime': origintime,
         'startdatetime': str(startdatetime)}
    bd = BaseDataDir(path)
    bd._write_jsondict(ChunkedSnd._chunkinfopath, d=d,
                       overwrite=overwrite)
    if metadata is not None:
        bd._write_jsondict(ChunkedSnd._metadatapath, d=dict(metadata),
                           overwrite=overwrite)
    return ChunkedSnd(path)







