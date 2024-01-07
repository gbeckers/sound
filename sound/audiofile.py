import numpy as np
import soundfile as sf
from contextlib import contextmanager
from pathlib import Path
from .sndinfo import SndInfo, _create_sndinfo
from .snd import BaseSnd
from .utils import wraptimeparamsmethod

__all__ = ["AudioSnd", "availableaudioformats", "availableaudioencodings"]

defaultaudioformat = 'WAV'
defaultaudioencoding = {'AIFF': 'PCM_24',
                        'AU': 'PCM_24',
                        'AVR': 'PCM_16',
                        'CAF': 'PCM_24',
                        'FLAC': 'PCM_24',
                        'HTK': 'PCM_16',
                        'IRCAM': 'FLOAT',
                        'MAT4': 'FLOAT',
                        'MAT5': 'FLOAT',
                        'MPC2K': 'PCM_16',
                        'NIST': 'PCM_24',
                        'OGG': 'VORBIS',
                        'PAF': 'PCM_24',
                        'PVF': 'PCM_32',
                        'RAW': 'FLOAT',
                        'RF64': 'PCM24',
                        'SD2': 'PCM_24',
                        'SDS': 'PCM_24',
                        'SVX': 'PCM_16',
                        'VOC': 'PCM_16',
                        'W64': 'PCM_24',
                        'WAV': 'PCM_24',
                        'WAVEX': 'PCM_24',
                        'WVE': 'ALAW',
                        'XI': 'DPCM_16'}

audiofloat_to_PCM_factor = {
    'PCM_32': 0x7FFFFFFF,     # 2147483647
    'PCM_24': 0x7FFFFF,     # 8388607
    'PCM_16': 0x7FFF,     # 32767
    'PCM_S8': 0x7F,     # 127
    'PCM_U8': 0xFF,     # 255
}

PCM_32_to_audiofloat_factor = {
    'PCM_32': 1 / 0x80000000, # 1 / 2147483648
    'PCM_24': 1 / 0x800000, # 1 / 8388607
    'PCM_16': 1 / 0x8000, # 1 / 32767
    'PCM_S8': 1 / 0x80, # 1 / 127
    'PCM_U8': 1 / 0xFF, # 1 / 255
}

_sfformats = sf.available_formats()
_sfsubtypes = sf.available_subtypes()
_audioformatkeys = sorted(list(_sfformats.keys()))
_audioencodingkeys = sorted(list(_sfsubtypes.keys()))
availableaudioformats = {key: _sfformats[key] for key in _audioformatkeys}
availableaudioencodings = {key: _sfsubtypes[key] for key in _audioencodingkeys}

# The choices for default dtypes for the different encodings is based on how
# the data is read in libsndfile most directly. I figured this out by looking
# at libsndfile source code.
#     ALAC: Apple Lossless Audio Codec, libsndfile uses int32
#     ALAW: A-Law telephony companding algorithm, libsndfile uses int16
#     DPCM: Differential pulse-code modulation, libsndfile uses ints
#     DWVW: Delta with variable word width, libsndfile uses ints
#     G721_32: Adaptive differential pulse code modulation, libsndfile uses int16
#     GSM610
#     IMA_ADPCM: Interactive Multimedia Association ADPCM, libsndfile uses int16
#     MS_ADPCM
#     ULAW:  μ-law algorithm, libsndfile uses int16
#     VORBIS: libsndfile uses float32
#     VOX_ADPCM: Dialogic ADPCM, libsndfile uses int16
encodingtodtype = {'ALAC_16': 'int16',
                   'ALAC_20': 'int32',
                   'ALAC_24': 'int32',
                   'ALAC_32': 'int32',
                   'ALAW': 'int16',
                   'DOUBLE': 'float64',
                   'DPCM_16': 'int16',
                   'DPCM_8': 'int16',
                   'DWVW_12': 'int16',
                   'DWVW_16': 'int16',
                   'DWVW_24': 'int32',
                   'FLOAT': 'float32',
                   'G721_32': 'int16',
                   'G723_24': 'int16',
                   'GSM610': 'int16',
                   'IMA_ADPCM': 'int16',
                   'MS_ADPCM': 'int16',
                   'PCM_S8': 'int16',
                   'PCM_U8': 'int16',
                   'PCM_16': 'int16',
                   'PCM_24': 'int32',
                   'PCM_32': 'int32',
                   'ULAW': 'int16',
                   'VORBIS': 'float32',
                   'VOX_ADPCM': 'int16'}

class AudioFile(BaseSnd, SndInfo):

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
    fs
    startdatetime
    origintime
    metadata
    accessmode
    scalingfactor
    unit


    """

    _classid = 'AudioFile'
    _classdescr = 'Sound in audio file plus optionally metadata in json file'
    _settableparams = ('fs', 'metadata', 'origintime', 'scalingfactor',
                       'startdatetime', 'unit')

    def __init__(self, path, accessmode='r'):
        audiofilepath, sndinfopath = self._check_path(path)
        self._audiofilepath = audiofilepath
        self._mode = accessmode
        with sf.SoundFile(str(path)) as f:
            nframes = len(f)
            nchannels = f.channels
            fs = f.samplerate
            self._audiofileformat = f.format
            self._audioencoding = f.subtype
            self._framesdtype = encodingtodtype.get(f.subtype, 'float64') # if we do not know, we just play safe
            self._endianness = f.endian
        SndInfo.__init__(self, path=sndinfopath, accessmode=accessmode,
                         settableparams=self._settableparams)
        si = self._sndinfo._read()
        kwargs = {sp: si.get(sp, None) for sp in self._settableparams}
        if 'fs' in kwargs:
            fs = kwargs['fs']
            del kwargs['fs']
        BaseSnd.__init__(self, nframes=nframes, nchannels=nchannels, fs=fs,
                         setparamcallback=self._set_parameter, **kwargs)
        self._fileobj = None

    def __str__(self):
        return f'{super().__str__()[:-1]}, {self.fileformat} ' \
               f'{self.fileformatsubtype}>'

    __repr__ = __str__

    @property
    def audiofilepath(self):
        return self._audiofilepath

    @property
    def mode(self):
        return self._mode

    @property
    def framesdtype(self):
        """numpy dtype of frames that the `read_frames` method returns"""
        return self._framesdtype

    @property
    def fileformat(self):
        return self._audiofileformat

    @property
    def fileformatsubtype(self):
        return self._audioencoding

    @property
    def endianness(self):
        return self._endianness

    def _check_path(self, path):
        path = Path(path)
        if path.suffix.upper()[1:] in availableaudioformats:
            sndinfopath = Path(f'{path}{SndInfo._suffix}')
            audiopath = path
        elif path.suffix in (SndInfo._suffix, SndInfo._suffix.upper()):  # we received info file, not audio file
            sndinfopath = path
            audiopath = path.parent / path.stem
        elif not path.exists():
            raise IOError(f"file {path} does not exist")
        else:
            raise IOError(f"file {path} not recognized as an audio file")
        return audiopath, sndinfopath

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

    def set_mode(self, mode):
        if not mode in {'r', 'r+'}:
            raise ValueError(f"'mode' must be 'r' or 'r+', not '{mode}'")
        self._mode = mode

    @wraptimeparamsmethod
    def read_frames(self, startframe=None, endframe=None, starttime=None,
                    endtime=None, startdatetime=None, enddatetime=None,
                    channelindex=None, out=None,
                    normalizeaudio=False):
        """Read audio frames (timesamples, channels) from file.

        A frames is a time sample that may be multichannel. The dtype cannot be chosen,
        and will be the closest compatible to the encoding type. Encodings based on integer
        numbers (e.g. PCM_16) will return int16 or int32 types (depending on bit depth
        of encoding), FLOAT encoding float32 and DOUBLE float64.

        Parameters
        ----------
        startframe
        endframe
        starttime
        endtime
        startdatetime
        enddatetime
        channelindex
        out
        normalizeaudio: bool, default: False
            Determines whether or not integer audio encodings such as PCM_16 should be normalized

        Returns
        -------

        """

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
                frames = af.read(endframe - startframe, dtype=self._framesdtype,
                                 always_2d=True, out=out)
            except:
                # TODO make a proper error
                print(f'Unexpected error when reading {endframe-startframe} frames, '
                      f'starting from frame {startframe} in {self.audiofilepath}, which should '
                      f'have {self.nframes} frames.')
                raise

            if channelindex is not None:
                frames = frames[:,channelindex]
            if normalizeaudio: # 'int32', 'int16'
                if frames.dtype == np.int32:
                    normfactor = 0x80000000
                elif frames.dtype == np.int16:
                    normfactor = 0x8000
                else:
                    raise TypeError(f"'normalizeaudio' parameter is "
                                    f"True, but can only be applied to int16 and "
                                    f"int32 data; received {frames.dtype} "
                                    f"data.")
                frames = frames.astype('float64')
                frames /= normfactor
            if self.scalingfactor is not None:
                frames = frames * self.scalingfactor
            return frames

    def info(self, verbose=False):
        d = super().info()
        d['fileformat'] = self.fileformat
        d['audiofilepath'] = str(self.audiofilepath)
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
        audiofilepath = self.audiofilepath
        sndinfopath = Path(f'{audiofilepath}{SndInfo._suffix}')
        d = self._saveparams  # standard params that need saving
        d.update({'endiannes': self.endianness,
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

    def __init__(self, path, accessmode='r'):
        path = Path(path)
        if path.suffix.upper()[1:] in availableaudioformats: # we received audio file, not info file
            sndinfopath = Path(f'{path}{SndInfo._suffix}')
        elif path.suffix in (SndInfo._suffix, SndInfo._suffix.upper()):
            sndinfopath = path
        else:
            raise IOError(f"file {path} does not exist")
        SndInfo.__init__(self, path=sndinfopath, accessmode=accessmode,
                         settableparams=self._settableparams)
        si = self._sndinfo._read()
        if si == {}: # there is no sndinfo file, we
            AudioFile.__init__(self, path=path,
                               setparamcallback=self._set_parameter)
        else:
            AudioFile.__init__(self, path=sndinfopath.parent / sndinfopath.stem,
                               fs=si['fs'], scalingfactor=si['scalingfactor'],
                               startdatetime=si['startdatetime'],
                               origintime=si['origintime'],
                               metadata=si['metadata'], accessmode=accessmode,
                               setparamcallback=self._set_parameter)

    def info(self, verbose=False):
        d = super().info()
        d['sndinfofilepath'] = str(self._sndinfo.audiofilepath)
        return {k: d[k] for k in sorted(d.keys())}


def audiocompatibilitytable_rst():
    """Creates a table with info on compatibility between audio formats and
    encodings.

    To be used for creating documentation.

    Returns
    -------
    str

    """
    maxaenckeylen = max(len(k) for k in _audioencodingkeys)
    sl = [] # stringlist
    # first line, horizontal border of table
    sl.append('+' + ((maxaenckeylen + 2) * '-') + '+')
    for formatkey in _audioformatkeys:
        sl.append(((len(formatkey) + 2) * '-') + '+')
    sl.append('\n')
    hborder = "".join(sl) # we need it after header row
    # header row
    sl.append(f'| ' + (maxaenckeylen * ' ') + ' |')
    for formatkey in _audioformatkeys:
        sl.append(f' {formatkey} |')
    sl.append(f"\n{hborder.replace('-','=')}")
    # next rows
    for enckey in _audioencodingkeys:
        # row label
        sl.append(f'| {enckey}' + ((maxaenckeylen - len(enckey)) * ' ') + ' |')
        # cols
        for formatkey in _audioformatkeys:
            if sf.check_format(formatkey, enckey):
                r = ' Y ' + ((len(formatkey) - 1) * ' ') + '|'
            else:
                r = ((len(formatkey) + 1 ) * ' ') + ' |'
            if enckey == defaultaudioencoding[formatkey]:
                r = r.replace('Y', 'D')
            sl.append(r)
        sl.append('\n')
        sl.append(hborder)
    sl.append("\nFormats: ")
    sl.extend([f'**{k}**: {l}, ' for k,l in availableaudioformats.items()])
    sl.append("\nEncodings: ")
    sl.extend([f'**{k}**: {l}, ' for k, l in availableaudioencodings.items()])
    sl.append('\n')
    return "".join(sl)