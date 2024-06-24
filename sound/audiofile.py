import numpy as np
import soundfile as sf
from contextlib import contextmanager
from pathlib import Path
from .sndinfo import SndInfo, _create_sndinfo
from .snd import BaseSnd, _cast_frames, _dtypetoencoding
from .utils import wraptimeparamsmethod

__all__ = ["AudioFile", "AudioFileMM", "availableaudioformats",
           "availableaudioencodings"]

defaultaudioformat = 'WAV'
# Unlike libsnd and soundfile, we do not directly support RAW as audio
# file. People should convert RAW to a DarrSnd
# TODO: create conversion function RAW to DarrSnd
defaultaudioencoding = {'AIFF': 'PCM_24',
                        'AU': 'PCM_24',
                        'AVR': 'PCM_16',
                        'CAF': 'PCM_24',
                        'FLAC': 'PCM_24',
                        'HTK': 'PCM_16',
                        'IRCAM': 'FLOAT',
                        'MAT4': 'FLOAT',
                        'MAT5': 'FLOAT',
                        'MP3': 'MPEG_LAYER_III',
                        'MPC2K': 'PCM_16',
                        'NIST': 'PCM_24',
                        'OGG': 'VORBIS',
                        'PAF': 'PCM_24',
                        'PVF': 'PCM_32',
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



_sfformats = sf.available_formats()
_sfsubtypes = sf.available_subtypes()
_audioformatkeys = sorted(list(_sfformats.keys()))
_audioencodingkeys = sorted(list(_sfsubtypes.keys()))
availableaudioformats = {key: _sfformats[key] for key in _audioformatkeys}
availableaudioencodings = {key: _sfsubtypes[key] for key in _audioencodingkeys}

# The choices for default dtypes for the different encodings is based on how
# the data is read in libsndfile.
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
                   'G723_40': 'int16',
                   'GSM610': 'int16',
                   'IMA_ADPCM': 'int16',
                   'MPEG_LAYER_I': 'float32',
                   'MPEG_LAYER_II': 'float32',
                   'MPEG_LAYER_III': 'float32',
                   'MS_ADPCM': 'int16',
                   'NMS_ADPCM_16': 'int16',
                   'NMS_ADPCM_24': 'int16',
                   'NMS_ADPCM_32': 'int16',
                   'OPUS': 'float32',
                   'PCM_S8': 'int16',
                   'PCM_U8': 'int16',
                   'PCM_16': 'int16',
                   'PCM_24': 'int32',
                   'PCM_32': 'int32',
                   'ULAW': 'int16',
                   'VORBIS': 'float32',
                   'VOX_ADPCM': 'int16'}


class _SFReader:

    def __init__(self, audiofilepath):
        self._audiofilepath = audiofilepath
        self._fileobj = None

    @contextmanager
    def _openfile(self):
        if self._fileobj is not None:
            yield self._fileobj
        else:
            try:
                with sf.SoundFile(str(self._audiofilepath),
                                  mode='r') as fileobj:
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

    def read_frames(self, startframe=None, endframe=None, channelindex=None,
                    out=None, dtype='float64'):
        """Read audio frames (timesamples, channels) from file.

        A frames is a time sample that may be multichannel.

        Parameters
        ----------
        startframe
        endframe
        channelindex
        out

        Returns
        -------

        """
        # for normalization we read as float64 so that we do not need to
        # convert later

        with self._openfile() as af:
            if startframe != af.tell():
                try:
                    af.seek(startframe)
                except:
                    # TODO make a proper error
                    print(f'Unexpected error when seeking frame '
                          f'{startframe} in {self._audiofilepath}')
                    raise
            try:
                frames = af.read(endframe - startframe, dtype=dtype,
                                 always_2d=True, out=out)
            except:
                # TODO create a proper error
                print(f'Unexpected error when reading {endframe - startframe} '
                      f'frames, starting from frame {startframe} in '
                      f'{self._audiofilepath}')
                raise
        if channelindex is not None:
            frames = frames[:, channelindex]
        return frames


class _MMReader:

    # WAV header entries have max 4 bytes = 32 bits
    _powers2 = np.power(2, np.arange(31, -1, -1, dtype='uint32'))

    def __init__(self, audiofilepath):
        self._audiofilepath = audiofilepath
        fmt = self.readformat()
        if fmt is None:
            raise TypeError(
                f"file {audiofilepath} does not seem to be an audio "
                f"file that supports memory mapping")
        self._memmap = None
        self._audiofd = None
        self._audioformat = fmt['audioformat']
        self._nframes = nframes = fmt['nframes']
        self._nchannels = nchannels= fmt['nchannels']
        self._shape = (nframes, nchannels)
        fs = fmt['fs']
        self._bitspersample = fmt['bitspersample']
        self._dataoffset = fmt['dataoffset']

        if self._audioformat == 3:  # FLOAT OR DOUBLE
            if self._bitspersample == 32:  # FLOAT
                self._dtype = '<f4'
            elif self._bitspersample == 64:  # DOUBLE
                self._dtype = '<f8'
            else:
                raise ValueError(f"bitspersample cannot be " 
                                 f"{self._bitspersample} for IEEE_FLOAT encoding" 
                                 f", only 32 or 64")
        elif self._audioformat == 1:
            if self._bitspersample == 8:
                self._dtype = f'<u1'
            elif self._bitspersample in (16, 32):
                self._dtype = f'<i{self._bitspersample // 8}'
            else:
                raise ValueError(f"bitspersample cannot be " 
                                 f"{self._bitspersample} for PCM encoding" 
                                 f", only 8, 16 or 32")
        else:
            raise ValueError(
                f"audio format {audioformat} not supported, only IEEE_FLOAT or PCM")


    @classmethod
    def bytestonum(cls, bytear):
        """Converts a little endian array of bytes as read by memmap from a wav
        file to a number"""
        bits = np.unpackbits(bytear[::-1])
        return sum(cls._powers2[-len(bits):] * bits)

    def readformat(self, verbose=False):
        """https://wavefilegem.com/how_wave_files_work.html"""
        bar = np.memmap(self._audiofilepath, dtype='B', offset=0)
        riffchunk = bar[:12]
        if not (riffchunk[:4].tobytes() == b'RIFF' \
                and riffchunk[8:12].tobytes() == b'WAVE'):
            if verbose:
                print(f"{path} does not seem to be a RIFF based WAVE file")
            return None
        fmtchunk = bar[
                   12:36]  # may be longer but 12:36 contains all the important parameters
        if not fmtchunk[:4].tobytes() == b'fmt ':
            raise ValueError(
                f'Unexpected wave file header format: bytes 12:16 should read '
                f'"fmt " but do in fact read "{fmtchunk[:4].tobytes()}"')
        # fmtchunk[4:8] fmt Subchunk1Size
        audioformat = self.bytestonum(fmtchunk[8:10])
        nchannels = self.bytestonum(fmtchunk[10:12])
        fs = self.bytestonum(fmtchunk[12:16])
        bitspersample = self.bytestonum(fmtchunk[22:24])
        start = 24
        while bar[start:start + 4].tobytes() != b'data':
            start += 4
        datasize = self.bytestonum(bar[start + 4:start + 8])
        dataoffset = start + 8
        nframes = datasize // nchannels // (bitspersample // 8)
        return {'audioformat': audioformat,
                'nframes': nframes,
                'nchannels': nchannels,
                'fs': fs,
                'bitspersample': bitspersample,
                'dataoffset': dataoffset}

    @contextmanager
    def _open(self):
        if self._memmap is not None:
            yield self._memmap, self._audiofd
        else:
            try:
                # we must do it like this instead of providing a filename
                # to np.mmemap, otherwise accessing temporary dirs on
                # windows will fail
                with open(file=self._audiofilepath, mode='r') as fd:
                    self._audiofd = fd
                    self._memmap = np.memmap(filename=fd,
                                             mode='r',
                                             shape=self._shape,
                                             dtype=self._dtype,
                                             order='C',
                                             offset=self._dataoffset)
                    yield self._memmap, self._audiofd
            except Exception:
                raise
            finally:
                if hasattr(self._memmap, '_mmap'):
                    self._memmap._mmap.close()  # *may need this for Windows*
                self._audiofd.close()
                self._memmap = None
                self._audiofd = None

    @contextmanager
    def open(self):
        with self._open() as (memmap, _):
            yield None

    # TODO out parameter
    def read_frames(self, startframe=None, endframe=None,
                    channelindex=None, out=None, dtype='float64'):

        with self._open() as (ar, _):
            frames = np.array(ar[slice(startframe,endframe, channelindex)],
                              dtype=dtype, copy=True)
        return frames


class AudioFile(BaseSnd, SndInfo):

    """Sound data stored in an audio file.

    Use this class to access data from audio files.

    And audio file may have a json-based sidecar file, with the extension
    '.snd', that contains additional metadata, and/or metadata that overrides
    metadata stored in the audio file.

    Parameters
    ----------
    path: str or pathlib.Path
    accessmode: 'r' or 'r+'
        determines if data in metadata sidecar file is writable or not

    """

    _classid = 'AudioFile'
    _classdescr = ('Sound in audio file potentially with metadata in sidecar '
                   'file')
    _settableparams = ('fs', 'metadata', 'origintime', 'scalingfactor',
                       'startdatetime', 'unit')
    _dtypes = ('float32', 'float64')
    _defaultdtype = 'float64'

    def __init__(self, path, accessmode='r', mmap=True):
        audiofilepath, sndinfopath = self._check_path(path)
        self._audiofilepath = audiofilepath
        self._mode = accessmode
        with sf.SoundFile(str(path)) as f:
            nframes = len(f)
            nchannels = f.channels
            fs = f.samplerate
            self._audiofileformat = af = f.format
            self._audioencoding = aenc = f.subtype
            self._endianness = f.endian
        if af == 'WAV' and aenc in ('FLOAT', 'DOUBLE') and mmap:
            self._audioreader = _MMReader(audiofilepath)
        else:
            self._audioreader = _SFReader(audiofilepath)
        SndInfo.__init__(self, path=sndinfopath, accessmode=accessmode,
                         settableparams=self._settableparams)
        si = self._sndinfo._read()
        kwargs = {sp: si[sp] for sp in self._settableparams if sp in si}
        if 'fs' in kwargs:
            fs = kwargs.pop('fs')
        BaseSnd.__init__(self, nframes=nframes, nchannels=nchannels, fs=fs,
                         sampledtype=self._defaultdtype,
                         setparamcallback=self._set_parameter, **kwargs)
        self._fileobj = None

    def __str__(self):
        return f'{super().__str__()[:-1]}, {self.fileformat} ' \
               f'{self.fileformatsubtype}, {self.sampledtype}>'

    __repr__ = __str__

    @property
    def audiofilepath(self):
        return self._audiofilepath

    @property
    def mode(self):
        return self._mode

    @property
    def fileformat(self):
        return self._audiofileformat

    @property
    def audioencoding(self):
        """Type of sample value encoding in audio file."""
        return self._audioencoding

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


    def set_mode(self, mode):
        if not mode in {'r', 'r+'}:
            raise ValueError(f"'mode' must be 'r' or 'r+', not '{mode}'")
        self._mode = mode

    @contextmanager
    def open(self):
        with self._audioreader.open():
            yield None

    @wraptimeparamsmethod
    def read_frames(self, startframe=None, endframe=None, starttime=None,
                    endtime=None, startdatetime=None, enddatetime=None,
                    channelindex=None, out=None, dtype='float64'):
        dtype = self._check_dtype(dtype)
        frames = self._audioreader.read_frames(startframe=startframe,
                                               endframe=endframe,
                                               channelindex=channelindex,
                                               out=out, dtype=dtype)
        if self.scalingfactor is not None:
            frames *= self.scalingfactor
        return frames

    def info(self, verbose=False):
        d = super().info()
        d['fileformat'] = self.fileformat
        d['audiofilepath'] = str(self.audiofilepath)
        d['audiofileencoding'] = str(self._audioencoding)
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