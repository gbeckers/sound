import shutil
import numpy as np
import soundfile as sf
from contextlib import contextmanager
from pathlib import Path
from .disksnd import create_datadir
from .snd import BaseSnd
from .disksnd import DataDir
from .utils import wraptimeparamsmethod
from ._version import get_versions

__all__ = ["AudioFile", "AudioSnd", "available_audioformats",
           "available_audioencodings"]

defaultaudioformat = 'WAV'
defaultaudiosubtype = {'AIFF': 'FLOAT',
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
    `as_audiofilesnd` method. An AudioFileSnd is based on the same audiofile,
    but in addition saves metadata and other information in separate
    text-based files.

    Parameters
    ----------
    filepath: str or pathlib.Path
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
    _version = get_versions()['version']


    def __init__(self, filepath, startdatetime='NaT', origintime=0.0,
                 metadata=None, mode='r', fs=None,
                 scalingfactor=None, unit=None, dtype=None):


        self.audiofilepath = Path(filepath)
        self._mode = mode
        with sf.SoundFile(str(filepath)) as f:
            nframes = len(f)
            nchannels = f.channels
            if fs is None: # possibility to override, e.g. floating point
                fs = f.samplerate
            self._fileformat = f.format
            self._fileformatsubtype = f.subtype
            self._endianness = f.endian
            if dtype is None:
                dtype = encodingtodtype.get(self._fileformatsubtype, 'float64')
        BaseSnd.__init__(self, nframes=nframes, nchannels=nchannels, fs=fs, dtype=dtype,
                         startdatetime=startdatetime, origintime=origintime, metadata=metadata,
                         encoding=f.subtype, scalingfactor=scalingfactor,
                         unit=unit)
        self._fileobj = None

    def __str__(self):
        return f'{super().__str__()[:-1]}, {self.fileformat} ' \
               f'{self.fileformatsubtype}>'

    __repr__ = __str__

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
                with sf.SoundFile(str(self.audiofilepath), mode=mode) as fileobj:
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
                    print(f'Unexpected error when seeking frame {startframe} in {self.audiofilepath} '
                          f'which should have {self.nframes} frames.')
                    raise
            try:
                frames = af.read(endframe-startframe, dtype=dtype,
                                  always_2d=True, out=out)
            except:
                # TODO make a proper error
                print(f'Unexpected error when reading {endframe-startframe} frames, '
                      f'starting from frame {startframe} in {self.audiofilepath}, which should '
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
        return sf.info(str(self.audiofilepath), verbose=verbose)

    # FIXME something like this also in Snd
    def as_audiosnd(self, outputpath=None, move=False,
                    overwrite=False):
        """Convert an AudioFile to a DiskAudioSnd

        Frama data will be based on the same underlying audiofile, either by
        copying the audio file (default) or moving it. The advantage of a
        DiskAudioSnd over an AudioFile is a.o. the ability to use metadata that
        is stored in a separate json text file and the ability to use
        non-integer sampling rates, a scaling factor, an non-default dtype,
        etc, in a persistent way.

        """
        audiofilepath = self.audiofilepath
        if outputpath is None:
            outputpath = audiofilepath.with_suffix(DataDir._suffix)
        if outputpath == audiofilepath:
            raise IOError(f"audiofile ({audiofilepath}) already has "
                          f"'.das' extension. Will not overwrite. Please "
                          f"specify an alternative outputpath")
        dd = create_datadir(outputpath, overwrite=overwrite)
        d = self._saveparams() # standard params that need saving
        d.update({'audiofilename': audiofilepath.name, # extra ones
                  'endiannes': self.endianness,
                  'fileformat': self.fileformat,
                  'objecttype': 'AudioSnd'})
        dd.write_sndinfo(d=d, overwrite=overwrite)
        if self.metadata is not None:
            dd.metadata.update(self.metadata)
        if move:
            shutil.move(audiofilepath, dd.path / audiofilepath.name)
        else:
            shutil.copy(audiofilepath, dd.path / audiofilepath.name)
        return AudioSnd(outputpath)


class AudioSnd(AudioFile):

    _classid = 'AudioSnd'
    _classdescr = 'disk-persistent sound in an audio file plus metadata'
    _version = get_versions()['version']

    def __init__(self, path, dtype=None, accessmode='r'):
        self._datadir = dd = DataDir(path=path, accessmode=accessmode)
        ci = dd.read_sndinfo()
        audiofilename = ci['audiofilename']
        if dtype is None:
            dtype = ci['dtype']
        AudioFile.__init__(self, filepath=dd.path / audiofilename,
                           fs=ci['fs'], scalingfactor=ci['scalingfactor'],
                           startdatetime=ci['startdatetime'],
                           origintime=ci['origintime'],
                           metadata=dd.metadata, mode='r', dtype=dtype)

    @property
    def datadir(self):
        return self._datadir


# FIXME get rid of this here, should move to BaseSnd
def to_audiofile(s, path=None, format=None, subtype=None,
                 endian=None,
                 startframe=None, endframe=None,
                 starttime=None, endtime=None,
                 startdatetime=None, enddatetime=None,
                 overwrite=False, channelindex=None):
    """
    Save sound object to an audio file.

    Parameters
    ----------
    s: Snd, DiskSnd, or AudioFile
    path
    format
    subtype
    endian
    startframe: {int, None}
        The index of the frame at which the exported sound should start.
        Defaults to None, which means the start of the sound (index 0).
    endframe: {int, None}
        The index of the frame at which the exported sound should start.
        Defaults to None, which means the start of the sound (index 0).
    starttime
    endtime
    startdatetime
    enddatetime
    overwrite
    channelindex

    Returns
    -------
    AudioFile object

    """
    if format is None:
        if isinstance(s, AudioFile):
            format = s._fileformat
        else:
            format = defaultaudioformat
    if subtype is None:
        if isinstance(s, AudioFile):
            if s._fileformatsubtype in sf.available_subtypes(format):
                subtype = s._fileformatsubtype
        else:
            subtype = defaultaudiosubtype[format]
    if path is None:
        if hasattr(s, 'path'):
            path = Path(s.audiofilepath)
        else:
            raise ValueError(f'`path` parameter must be specified for object of '
                             f'type {type(s)}')
    else:
        path = Path(path)
    if path.suffix != f'.{format.lower()}':
        path = path.with_suffix(f'.{format.lower()}')
    samplerate = round(s.fs)
    path = Path(path)
    if path.exists() and not overwrite:
        raise IOError(
            "File '{}' already exists; use 'overwrite'".format(path))
    startframe, endframe = s._check_episode(startframe=startframe,
                                            endframe=endframe,
                                            starttime=starttime,
                                            endtime=endtime,
                                            startdatetime=startdatetime,
                                            enddatetime=enddatetime)
    if channelindex is not None:
        nchannels = len(np.ones([1, s.nchannels])[0, channelindex])
    else:
        nchannels = s.nchannels
    with sf.SoundFile(file=str(path), mode='w', samplerate=samplerate,
                      channels=nchannels, subtype=subtype, endian=endian,
                      format=format) as f:
        for window in s.iterread_frames(blocklen=samplerate,
                                        startframe=startframe,
                                        endframe=endframe,
                                        channelindex=channelindex):
            f.write(window)

    return AudioFile(path)

