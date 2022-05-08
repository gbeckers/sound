import numpy as np
import soundfile as sf
from contextlib import contextmanager
from pathlib import Path
from .sndinfo import SndInfo, _create_sndinfo
from .snd import BaseSnd
from .utils import wraptimeparamsmethod

__all__ = ["AudioFile", "AudioSnd", "available_audioformats",
           "available_audioencodings"]

defaultaudioformat = 'WAV'
defaultaudioencoding = {'AIFF': 'FLOAT',
                        'AU': 'FLOAT',
                        'AVR': 'PCM_16',
                        'CAF': 'FLOAT',
                        'FLAC': 'PCM_24',
                        'HTK': 'PCM_16',
                        'IRCAM': 'FLOAT',
                        'MAT4': 'FLOAT',
                        'MAT5': 'FLOAT',
                        'MPC2K': 'PCM_16',
                        'NIST': 'PCM_32',
                        'OGG': 'VORBIS',
                        'PAF': 'PCM_24',
                        'PVF': 'PCM_32',
                        'RAW': 'FLOAT',
                        'RF64': 'FLOAT',
                        'SD2': 'PCM_24',
                        'SDS': 'PCM_24',
                        'SVX': 'PCM_16',
                        'VOC': 'PCM_16',
                        'W64': 'FLOAT',
                        'WAV': 'PCM_24',
                        'WAVEX': 'FLOAT',
                        'WVE': 'ALAW',
                        'XI': 'DPCM_16'}

available_audioformats = sf.available_formats()
available_audioencodings = sf.available_subtypes()


# because we read with soundfile, which only reads int16, int32, float32, float64
encodingtodtype = {'PCM_S8': 'int16',
                   'PCM_U8': 'int16',
                   'PCM_16': 'int16',
                   'PCM_24': 'int32',
                   'PCM_32': 'int32',
                   'FLOAT': 'float32',
                   'DOUBLE': 'float64'}


class AudioFile(BaseSnd):

    """Sound data stored in an audio file.

    Use this class to access data from audio files. Note that although you
    can provide additional info on the sound at instantiation, such as
    `startdatetime` and `metadata, or override the sampling rate, this info is
    not persistent (i.e. it is not saved on disk). If you want persistency
    then convert the AudioFile to an AudioFileSnd by using the
    `as_audiosnd` method. An AudioSnd is based on the same audiofile,
    but in addition saves metadata and other information in separate
    text-based files.

    Parameters
    ----------
    path: str or pathlib.Path
    dtype: numpy dtype, {'float32' | 'float64' | 'int16' | 'int32'| None}
    fs
    startdatetime
    origintime
    metadata
    mode
    scalingfactor
    unit


    """

    _classid = 'AudioFile'
    _classdescr = 'Sound in audio file'

    def __init__(self, path, startdatetime='NaT', origintime=0.0,
                 mode='r', fs=None, metadata=None, scalingfactor=None,
                 unit=None, dtype=None, **kwargs):
        self._path = Path(path)
        self._mode = mode
        with sf.SoundFile(str(path)) as f:
            nframes = len(f)
            nchannels = f.channels
            if fs is None: # possibility to override, e.g. floating point
                fs = f.samplerate
            self._fileformat = f.format
            self._fileformatsubtype = f.subtype
            self._endianness = f.endian
            if dtype is None:
                dtype = encodingtodtype.get(self._fileformatsubtype, 'float64')
        BaseSnd.__init__(self, nframes=nframes, nchannels=nchannels, fs=fs,
                         dtype=dtype, startdatetime=startdatetime,
                         origintime=origintime, metadata=metadata,
                         encoding=f.subtype, scalingfactor=scalingfactor,
                         unit=unit, **kwargs)
        self._fileobj = None

    def __str__(self):
        return f'{super().__str__()[:-1]}, {self.fileformat} ' \
               f'{self.fileformatsubtype}>'

    __repr__ = __str__

    @property
    def path(self):
        return self._path

    @property
    def mode(self):
        return self._mode

    @property
    def readdtype(self):
        return self._dtype

    @property
    def fileformat(self):
        return self._fileformat

    @property
    def fileformatsubtype(self):
        return self._fileformatsubtype

    @property
    def endianness(self):
        return self._endianness

    @contextmanager
    def _openfile(self, mode=None):
        if mode is None:
            mode = self._mode
        if self._fileobj is not None:
            yield self._fileobj
        else:
            try:
                with sf.SoundFile(str(self.path), mode=mode) as fileobj:
                    self._fileobj = fileobj
                    yield fileobj
            except:
                raise
            finally:
                self._fileobj = None


    @contextmanager
    def open(self):
        with self._openfile():
            yield None

    # def set_readdtype(self, dtype):
    #     self._dtype = dtype

    def set_mode(self, mode):
        if not mode in {'r', 'r+'}:
            raise ValueError(f"'mode' must be 'r' or 'r+', not '{mode}'")
        self._mode = mode

    # FIXME think about dtypes here: what should we allow
    @wraptimeparamsmethod
    def read_frames(self,  startframe=None, endframe=None, starttime=None,
                    endtime=None, startdatetime=None, enddatetime=None,
                    channelindex=None, dtype=None, out=None,
                    normalizeinttoaudiofloat=False):
        if dtype is None:
            dtype = self._dtype
        with self._openfile() as af:
            if startframe != af.tell():
                try:
                    af.seek(startframe)
                except:
                    #TODO make a proper error
                    print(f'Unexpected error when seeking frame {startframe} in {self.path} '
                          f'which should have {self.nframes} frames.')
                    raise
            try:
                frames = af.read(endframe-startframe, dtype=dtype,
                                  always_2d=True, out=out)
            except:
                # TODO make a proper error
                print(f'Unexpected error when reading {endframe-startframe} frames, '
                      f'starting from frame {startframe} in {self.path}, which should '
                      f'have {self.nframes} frames.')
                raise

            if channelindex is not None:
                frames = frames[:,channelindex]
            if normalizeinttoaudiofloat: # 'int32', 'int16'
                if frames.dtype == np.int32:
                    frames *= 1 / 0x80000000
                elif frames.dtype == np.int16:
                    frames *= 1 / 0x8000
                else:
                    raise TypeError(f"'normalizeinttoaudiofloat' parameter is "
                                    f"True, but can only applied to int16 and "
                                    f"int32 data; received {frames.dtype} "
                                    f"data.")
            if self.scalingfactor is not None:
                frames *= self.scalingfactor
            return frames

    def info(self, verbose=False):
        d = super().info()
        d['fileformat'] = self.fileformat
        d['audiofilepath'] = str(self.path)
        return {k: d[k] for k in sorted(d.keys())}

    def as_audiosnd(self, accessmode='r', overwrite=False):
        """Convert an AudioFile to an AudioSnd

        Frama data will be based on the same underlying audiofile,
        but additional info will be saved separately. The advantage of a
        AudioSnd over an AudioFile is a.o. the ability to use metadata that
        is stored in a separate json text file and the ability to use
        non-integer sampling rates, a scaling factor, an non-default dtype,
        etc, in a persistent way.

        """
        if self.metadata is None:
            metadata = {}
        else:
            metadata = self.metadata
        audiofilepath = self.path
        sndinfopath = audiofilepath.with_suffix(SndInfo._suffix)
        d = self._saveparams  # standard params that need saving
        d.update({'audiofilename': audiofilepath.name, # extra ones
                  'endiannes': self.endianness,
                  'fileformat': self.fileformat,
                  'metadata': metadata,
                  'sndtype': AudioSnd._classid,
                  })
        _create_sndinfo(sndinfopath, d=d, overwrite=overwrite)
        return AudioSnd(sndinfopath, accessmode=accessmode)


class AudioSnd(AudioFile, SndInfo):

    _classid = 'AudioSnd'
    _classdescr = 'Sound in audio file plus additional data in json file'
    _settableparams = ('fs', 'metadata', 'origintime', 'scalingfactor',
                      'startdatetime', 'unit')

    def __init__(self, path, dtype=None, accessmode='r'):
        path = Path(path)
        SndInfo.__init__(self, path=path, accessmode=accessmode,
                         settableparams=self._settableparams)
        si = self._sndinfo._read()
        audiofilename = path.parent / si['audiofilename']
        if dtype is None:
            dtype = si['dtype']
        AudioFile.__init__(self, path=audiofilename,
                           fs=si['fs'], scalingfactor=si['scalingfactor'],
                           startdatetime=si['startdatetime'],
                           origintime=si['origintime'],
                           metadata=si['metadata'], mode=accessmode,
                           dtype=dtype, setparamcallback=self._set_parameter)

    def info(self, verbose=False):
        d = super().info()
        d['sndinfofilepath'] = str(self._sndinfo.path)
        return {k: d[k] for k in sorted(d.keys())}

