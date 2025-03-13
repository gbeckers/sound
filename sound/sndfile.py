import os
import numpy as np
import warnings
from contextlib import contextmanager, ExitStack
from pathlib import Path
from .audiofile import AudioFile
from .sndinfo import SndInfo, _create_sndinfo
from .snd import BaseSnd, _cast_frames, _dtypetoencoding
from .utils import wraptimeparamsmethod, duration_string
from .check_arg import check_arg

__all__ = ["SndFile", "SndChannelFiles"]

class SndFile(BaseSnd, SndInfo):

    """Sound data stored in an audio file, potentially with metadata
    in sidecar file.

    Use this class to access data from single audio files.

    And audio file may have a json-based sidecar file, with the extension
    '.snd', that contains additional metadata, and/or metadata that overrides
    metadata stored in the audio file.

    Parameters
    ----------
    path: str or pathlib.Path
    accessmode: 'r' or 'r+'
        determines if data in metadata sidecar file is writable or not

    """

    _classid = 'SndFile'
    _classdescr = ('Sound in audio file with metadata in json sidecar '
                   'file')
    _sampledtypes = ('float32', 'float64')
    _defaultsampledtype = 'float32'

    _setableparams = ('origintime', 'samplingrate', 'scalingfactor',
                          'startdatetime', 'unit', 'usermetadata')

    def __init__(self, path, accessmode='r'):
        path = self._check_path(path)
        self._mode = self.set_mode(accessmode)
        SndInfo.__init__(self, path=path, accessmode=accessmode)
        si = self._sndinfo._read()
        afp = (path / Path(si['sndinfo']['audiofilepath'])).resolve()
        af = AudioFile(afp)
        nframes = af.nframes
        nchannels = af.nchannels
        samplingrate = si['sndmetadata'].pop('samplingrate') # we override af samplingrate
        kwparams = {}
        kwparams.update(si['sndmetadata'])
        kwparams.update(si['recordingdata'])
        BaseSnd.__init__(self, nframes=nframes, nchannels=nchannels,
                         samplingrate=samplingrate,
                         setparamcallback=self._set_parameter,
                         **kwparams)
        self._filepath = path
        self._audiofile = af
        self._audiofilepath = afp

    @property
    def audiofilepath(self):
        return self._audiofilepath
    @property
    def _saveparams(self):
        d = super()._saveparams
        d['sndinfo']['audiofilepath'] = self._audiofilepath.relative_to(self.filepath.absolute(), walk_up=True)
        d['audiofileinfo'] = afi =  {}
        afi.update({'encoding': self._audiofile._encoding,
                    'fileformat': self._audiofile._fileformat})
        afi['metadata'] = {}
        for amd in ('bext', 'iXML', 'olym'):
            if amd in self._audiofile.metadata:
                afi['metadata'][amd] = self._audiofile.metadata[amd].to_dict()
        return d

    # @property
    # def _savedict(self):
    #     d = {'audiofilepath':  self._audiofilepath.relative_to(self.filepath.absolute(), walk_up=True)}
    #     d.update(self._saveparams)
    #     return d


    def __str__(self):
        return f'{super().__str__()[:-1]}, {self._filepath}>'

    __repr__ = __str__

    @property
    def filepath(self):
        """Path to Snd file."""
        return self._filepath

    @property
    def audiofile(self):
        """AudioFile object."""
        return self._audiofile

    @property
    def mode(self):
        return self._mode

    def _check_path(self, path):
        """Returns correct path of sndinfo file"""
        path = Path(path)
        if path.suffix in (SndInfo._suffix, SndInfo._suffix.upper(), SndInfo._suffix.lower()):
            sndinfopath = path
        elif not path.exists():
            raise IOError(f"file {path} does not exist")
        else:# we probably received audio file, not info file
            sndinfopath = path.with_suffix(SndInfo._suffix)
        return sndinfopath


    def set_mode(self, mode):
        if not mode in {'r', 'r+'}:
            raise ValueError(f"'mode' must be 'r' or 'r+', not '{mode}'")
        self._mode = mode

    @contextmanager
    def open(self):
        with self._audiofile.open():
            yield None

    @wraptimeparamsmethod
    def read_frames(self, startframe=None, endframe=None, starttime=None,
                    endtime=None, startdatetime=None, enddatetime=None,
                    channelindex=None, out=None, dtype=None):
        if dtype is None:
            dtype = self._defaultsampledtype
        dtype = self._check_dtype(dtype)
        frames = self._audiofile.read_frames(startframe=startframe,
                                               endframe=endframe,
                                               channelindex=channelindex,
                                               out=out, dtype=dtype)
        if self.scalingfactor is not None:
            frames *= self.scalingfactor
        return frames

    def info(self, verbose=False):
        d = self._saveparams
        return d



class SndChannelFiles(BaseSnd, SndInfo):
    """Continuous sound with time-aligned channels stored in separate mono audio
    files.

    """
    _classid = 'SndChannelFiles'
    _classdescr = ('')

    def __init__(self, path, accessmode='r'):
        SndInfo.__init__(self, path=path, accessmode=accessmode,
                         setableparams=SndFile._settableparams)
        self._channeldirpath = self._sndinfo.path.parent
        si = self._sndinfo._read()
        kwargs = {sp: si[sp] for sp in self._settableparams if sp in si}
        if 'fs' in kwargs:
            fs = kwargs.pop('fs')
        self._snds = []
        for pathname in si['channelfilepaths']:
            snd = SndFile(self._channeldirpath / pathname)
            self._snds.append(snd)
        BaseSnd.__init__(self, nframes=si['nframes'],
                         nchannels=si['nchannels'],
                         samplingrate=si['fs'], sampledtype=si['sampledtype'],
                         setparamcallback=self._set_parameter, **kwargs)

    @property
    def audiofilepaths(self):
        return [s.audiofilepath for s in self._snds]

    @property
    def mode(self):
        return self._mode

    @property
    def fileformats(self):
        return [s._audiofileformat for s in self._snds]

    @property
    def audioencodings(self):
        """Type of sample value encoding in audio files."""
        return [s._audioencoding for s in self._snds]

    @contextmanager
    def open(self):
        with ExitStack() as stack:
            ahs = [stack.enter_context(s.open()) for s in self._snds]
            yield None

    @wraptimeparamsmethod
    def read_frames(self, startframe=None, endframe=None, starttime=None,
                    endtime=None, startdatetime=None, enddatetime=None,
                    channelindex=None, dtype='float64'):
        nframes = endframe -startframe
        if channelindex is None:
            snds = self._snds
        else:
            snds = self._snds[channelindex]
        frames = np.empty((nframes,len(snds)), dtype=dtype)
        for chn, s in enumerate(snds):
            frames[:,[chn]] = s.read_frames(startframe=startframe,
                                          endframe=endframe,
                                          dtype=dtype)
        return frames



