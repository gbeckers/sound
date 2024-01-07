import numpy as np
from contextlib import contextmanager
from darr.basedatadir import BaseDataDir
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
    _classdescr = 'represents a continuous sound stored in separate files'
    _suffix = '.chunkedsnd'
    _fileformat = 'chunkedsnd'

    def __init__(self, path, dtype=None, accessmode='r'):
        SndInfo.__init__(self, path=path, accessmode=accessmode)
        self._snds = []
        chunknframes = [0]
        ci = self._read_jsondict(self._sndinfopath)
        if ci['filetype'] == 'AudioFile':
            SndClass = AudioFile
        elif ci['filetype'] == 'DarrSnd':
            SndClass = DarrSnd
        else:
            raise TypeError(f"file type '{ci['filetype']}' not understood")
        for pn in ci['chunkpaths']:
            snd = SndClass(self.path / pn, dtype=dtype)
            self._snds.append(snd)
            chunknframes.append(snd.nframes)
        self._chunknframes = np.array(chunknframes, dtype='int64')
        self._endindices = np.cumsum(self._chunknframes)
        nframes = self._chunknframes.sum()
        nchannels = ci['nchannels']
        if dtype is None:
            dtype = ci['dtype']
        BaseSnd.__init__(self, nframes=nframes, nchannels=nchannels, fs=ci['fs'],
                         dtype=dtype,
                         startdatetime=ci['startdatetime'],
                         origintime=ci['origintime'], metadata=self.metadata,
                         encoding=ci['fileformatsubtype'])

    @contextmanager
    def open(self):
        yield None # still to be implemented

    @wraptimeparamsmethod
    def read_frames(self, startframe=None, endframe=None, starttime=None,
                    endtime=None, startdatetime=None, enddatetime=None,
                    channelindex=None, dtype=None, normalizeaudio=False):
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
    sndinfo = list_audiofiles(path, extensions=(extension,), recursive=False)
    #FIXME assert same sound types
    subtype = sndinfo['subtype'][0]
    if dtype is None:
        dtype = encodingtodtype.get(subtype, 'float64')
    startdatetime = np.datetime64(startdatetime)
    d = {'filetype': 'AudioFile',
         'chunkpaths': sndinfo['paths'],
         'fs': sndinfo['fs'][0],
         'fileformat': sndinfo['fileformat'][0],
         'fileformatsubtype': sndinfo['subtype'][0],
         'endiannes': sndinfo['endianness'][0],
         'dtype': dtype,
         'nchannels': sndinfo['nchannels'][0],
         'origintime': origintime,
         'startdatetime': str(startdatetime)}
    bd = BaseDataDir(path)
    bd._write_jsondict(ChunkedSnd._sndinfopath, d=d,
                       overwrite=overwrite)
    if metadata is not None:
        bd._write_jsondict(ChunkedSnd._metadatapath, d=dict(metadata),
                           overwrite=overwrite)
    return ChunkedSnd(path)







