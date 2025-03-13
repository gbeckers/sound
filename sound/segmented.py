import numpy as np
from pathlib import Path
from contextlib import contextmanager, ExitStack
from darr.basedatadir import DataDir
from darr.metadata import MetaData
from .snd import BaseSnd
from .sndinfo import SndInfo
from .sndfile import SndFile
from .audiofile import AudioFile
from .utils import wraptimeparamsmethod, duration_string
from .audioimport import list_audiofiles
from ._version import get_versions


__all__ = ['SegmentedSndFiles']


# Are there things shared between disk-based objects that justify a Subclass
# of BaseSnd?

# Takes too long to load. Is it opening files audio? Just check if they exist.

class SegmentedSndFiles(BaseSnd, SndInfo):

    _classid = 'SegmentedSndFiles'
    _classdescr = ('represents a continuous sound stored in separate, '
                   'contiguous audio files')
    _suffix = '.sound'
    _settableparams = ('fs', 'metadata', 'origintime', 'scalingfactor',
                       'startdatetime', 'unit')
    _sampledtypes = ('float32', 'float64')
    _defaultsampledtype = 'float32'
    _sndinfopath = 'snd_metadata.json'
    _metadatapath = 'user_metadata.json'

    def __init__(self, path, accessmode='r', mmap=True):
        sndinfopath = self._check_path(path)
        self._segmentdirpath = sndinfopath.parent
        SndInfo.__init__(self, path=sndinfopath, accessmode=accessmode,
                         setableparams=self._settableparams)
        self._snds = []
        ci = self._sndinfo._read()
        self._nsegments = len(ci['segmentfilepaths'])
        if ci['segmenttype'] == 'SndFile':
            SndClass = SndFile
        else:
            raise TypeError(f"Sound object type '{ci['filetype']}' not "
                            f"understood")
        for pathname in ci['segmentfilepaths']:
            snd = SndClass(self._segmentdirpath / pathname, mmap=mmap)
            self._snds.append(snd)
        self._segmentnframes = np.array(ci['segmentnframes'], dtype='int64')
        self._startendindices = np.cumsum(np.array([0] + ci['segmentnframes'], dtype='int64'))
        self._audiofilepaths = [self._segmentdirpath/ Path(p)
                                for p in ci['segmentfilepaths']]
        nframes = self._segmentnframes.sum()
        nchannels = ci.pop('nchannels')
        dtype = ci.pop('sampledtype')
        fs = ci.pop('fs')
        kwargs = {sp: ci[sp] for sp in self._settableparams if sp in ci}
        BaseSnd.__init__(self, nframes=nframes, nchannels=nchannels, samplingrate=fs,
                         sampledtype=dtype,
                         setparamcallback=self._set_parameter, **kwargs)

    @property
    def segmentfilepaths(self):
        return self._audiofilepaths

    @property
    def segmentdirpath(self):
        return self._segmentdirpath

    @property
    def segmentindices(self):
        return [list(self._startendindices[i:i+2]) for i in range(self.nsegments)]

    @property
    def nsegments(self):
        return self._nsegments

    def _check_path(self, path):
        path = Path(path)
        if not path.exists():
            raise IOError(f"SegmentedSndFiles path {path} does not exist")
        return path

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
        startchunk, endchunk = np.searchsorted(self._startendindices, (startframe, endframe), side="right") - (1, 1)
        startframe -= self._startendindices[startchunk]
        endframe -= self._startendindices[endchunk]
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


class SegmentedSndChannelFiles(BaseSnd, SndInfo):
    """Continuous sound with time-aligned channels stored in separate mono audio
       files that are segmented in a series of contiguous files. This type of
       storage is used in recorders that save channels as mono audio files,
       which are segmented when file size reaches a maximum (in practce often
       2.1 or 4.2 Gb). E.g.:

       segment1_channel1.wav
       segment1_channel2.wav
       segment2_channel1.wav
       segment2_channel2.wav
       segment3_channel1.wav
       segment3_channel2.wav

       Channels withing segments are time-aligned. Segments are contiguous in
       the time domain.

       """
    _classid = 'SegmentedSndChannelFiles'
    _classdescr = ('')

    def __init__(self, path, accessmode='r'):
        SndInfo.__init__(self, path=path, accessmode=accessmode,
                         setableparams=SndFile._setableparams)
        self._channeldirpath = self._sndinfo.path.parent
        si = self._sndinfo._read()
        kwargs = {sp: si[sp] for sp in self._settableparams if sp in si}
        samplingrate = si['samplingrate']
        startdatetime = np.datetime64(si['startdatetime'])
        segs = []
        segpaths = []
        segstartdatetimes = []
        totalnframes = 0
        for chpaths in si['filepaths']:
            channels = []
            channelpaths = []
            for chpath in chpaths:
                af = AudioFile(self._channeldirpath / chpath)
                channels.append(af)
                channelpaths.append(self._channeldirpath / chpath)
            segs.append(tuple(channels))
            segpaths.append(tuple(channelpaths))
            if not np.isnat(startdatetime):
                segstartdatetimes.append(startdatetime + np.round(
                    1e9 * totalnframes / samplingrate).astype(
                    'timedelta64[ns]'))
            else:
                segstartdatetimes.append(startdatetime)
            totalnframes += channels[0].nframes


        self._audiofiles = tuple(segs)
        self._audiofilepaths = tuple(segpaths)
        BaseSnd.__init__(self, nframes=totalnframes,
                         nchannels=si['nchannels'],
                         samplingrate=samplingrate,
                         sampledtype=si['sampledtype'],
                         setparamcallback=self._set_parameter, **kwargs)

    @property
    def audiofiles(self):
        return self._audiofiles

    @property
    def audiofilepaths(self):
        return self._audiofilepaths

    @property
    def mode(self):
        return self._mode

    @property
    def fileformats(self):
        return [[ch._audiofileformat for ch in seg] for seg in self._audiofiles]

    @property
    def audioencodings(self):
        """Type of sample value encoding in audio files."""
        return [[ch._audioencoding for ch in seg] for seg in self._audiofiles]

    @property
    def endiannesses(self):
        return [[ch._audioendianness for ch in seg] for seg in self._audiofiles]







