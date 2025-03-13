import os
import numpy as np
from pathlib import Path
from contextlib import contextmanager
from .riffdata import RIFFFile
from .check_arg import check_arg
from .utils import duration_string, wraptimeparamsmethod, check_episode

##################################
## Useful info on audio formats ##
##################################

# BWF:  https://tech.ebu.ch/docs/tech/tech3285.pdf
# RF64: https://tech.ebu.ch/docs/tech/tech3306v1_0.pdf
# MBWF/RF64: https://tech.ebu.ch/docs/tech/tech3306v1_1.pdf
# Python modules for handling the Broadcast Wave Format and RF64 files:
#    https://github.com/nrkno/wave-bwf-rf64
# Package allows you to probe WAVE and RF64/WAVE files and extended metadata:
#    https://github.com/iluvcapra/wavinfo

# https://github.com/QutEcoacoustics/emu
# sample files https://www.mmsp.ece.mcgill.ca/Documents/AudioFormats/WAVE/Samples.html
# Explanation wave files: https://wavefilegem.com/how_wave_files_work.html
# Wave reference book: https://wavref.til.cafe/

##################################

# only non-compressed WAVE files (including BWF ) are natively supported
# other formats and encodings by libsndfile in separate module
supported_fileformats = {
    'WAV': 'WAV (Microsoft)',
}

# we follow terminology from soundfile library
supported_encodings = {
    'PCM_S8': 'Signed 8 bit PCM',
    'PCM_16': 'Signed 16 bit PCM',
    'PCM_24': 'Signed 24 bit PCM',
    'PCM_32': 'Signed 32 bit PCM',
    'PCM_U8': 'Unsigned 8 bit PCM',
    'FLOAT': '32 bit float',
    'DOUBLE': '64 bit float',
}

PCMvalue_to_audiofloat_factor = {
    'PCM_32': 1 / 0x80000000, # 1 / 2147483648
    'PCM_24': 1 / 0x800000, # 1 / 8388608
    'PCM_16': 1 / 0x8000, # 1 / 32768
    'PCM_S8': 1 / 0x80, # 1 / 128
    'PCM_U8': 1 / 0xFF, # 1 / 255
}


class WAVFileError(Exception):
    def __init__(self, message):
        self.message = message

class AudioMetadata:
    pass

# Note for future work:
# - include RF64 and Wave64? Probably not. Seems not to be used a lot
# - include WAVFORMATEXTENSIBLE? Don't know how common this is


class BaseWAVEFile(RIFFFile):
    """
    Base class for WAVE files. Does not read sound data, but does read metadata
    from RIFF chunks.

    """

    def __init__(self, filepath):
        RIFFFile.__init__(self, filepath)
        if self._formtype != 'WAVE':
            raise WAVFileError(f'File does not seem to be a WAVE file '
                               f'(form type: {self._formtype}).')
        # WAVE files should always have a 'fmt' chunk with audio metadata
        fmt = self.get_chunk('fmt')
        tag = fmt.tag
        if tag == 65534: #  WAVE_FORMAT_EXTENSIBLE, need to look for format in extension part
            tag = fmt.subformatGUID[:2]
            tag = self._bytestoint(tag)
            # TODO channelmask
        self._tag = tag
        self._nchannels = fmt.nchannels
        self._samplingrate = fmt.samplingrate
        self._nbits = fmt.nbits
        self._blocksize = fmt.blocksize
        start, size = self.chunklocations['data']  # of the data chunk, not data
        self._audiodataoffset = check_arg(start + 8, 'dataoffset') # data chunk + header
        self._audiodatasize = check_arg(size - 8, 'datasize')
        if self._tag in (1,3): # uncompressed data, don't need fact chunk info
            nframes = self._audiodatasize // self._blocksize
        else:
            fact = self.get_chunk('fact')
            nframes = fact.nframes
        self._nframes = nframes
        self._datashape = (self._nframes, self._nchannels)
        self._fileformat = 'WAV'

    @property
    def tag(self):
        return self._tag

    @property
    def nchannels(self):
        return self._nchannels

    @property
    def samplingrate(self):
        return self._samplingrate

    @property
    def nbits(self):
        return self._nbits

    @property
    def blocksize(self):
        return self._blocksize

    # TODO check if this means only byteorder
    @property
    def endianness(self):
        return 'LITTLE'

    @property
    def audiodataoffset(self):
        """start of audio data in number of bytes from beginning of file"""
        return self._audiodataoffset

    @property
    def audiodatasize(self):
        """size of audio data in number of bytes"""
        return self._audiodatasize

    @property
    def nframes(self):
        return self._nframes

    @property
    def datashape(self):
        return self._datashape

    @property
    def metadata(self):
        d = {}
        for key in self.chunklocations:
            if key != 'data':  # don't read audio data chunk, can be big
                d[key] = self.get_chunk(key)
        return d

    @property
    def fileformat(self):
        return self._fileformat

    def __str__(self):
        return (f"<WAVE file '{self.filepath.name}': "
                f"{duration_string(self._nframes / self._samplingrate)}, "
                f"{self._nchannels} channels>")

    __repr__ = __str__



class WAVEFileAudioReader(BaseWAVEFile):

    """Read WAVE PCM and IEEE_FLOAT files

    Supported encodings for WAVE files of linear PCM type (WAVE_FORMAT_PCM):
    PCM_U8: Unsigned 8 bit PCM
    PCM_16: Signed 16 bit PCM
    PCM_24: Signed 24 bit PCM
    PCM_32: Signed 32 bit PCM

    Supported encodings for WAVE files of IEEE_FLOAT type (WAVE_FORMAT_IEEE_FLOAT):
    FLOAT: 32-bit float
    DOUBLE: 64-bit float

    Sound has its own code for reading WAVE files because they are most
    commonly used in science or nature/sound scape recording. This way, hard
    dependencies on exteral libraries are seriously reduced. Also, this class
    supports reading header info (metadata RIFF child chunks) more  extensively
    than other libraries. Audio/field recorders often store useful metadata in
    such RIFF chunks, such as type of equipment, settings, datetime, and
    sometimes event markers.

    Sound does not natively support WAVE files with compressed audio data or
    non-WAVE files, but will read those files if the `soundfile` library is
    installed.

    The WAVEFileReader class should normally not be used directly by users. Use
    the AudioFile class for all audio files and `sound` will determine how best
    to read them.

    """

    def __init__(self, filepath):
        BaseWAVEFile.__init__(self, filepath)
        if self.tag not in (1,3): # 1 is integer LPCM, 3 is floating point LPCM
            raise WAVFileError(f'WAVE format tag is "{self.tag}". Only "1" '
                               f'(uncompressed integer data) is supported.')
        match self.nbits:
            case 8:
                encoding = 'PCM_U8'
            case 16:
                encoding = 'PCM_16'
            case 24:
                encoding = 'PCM_24'
            case 32:
                if self.tag == 1:
                    encoding = 'PCM_32'
                else:  # tag == 3
                    encoding = 'FLOAT'
            case 64:  # PCM_64 does not exist
                if self.tag == 3:
                    encoding = 'DOUBLE'
                else:
                    raise WAVFileError(
                        f'format chunk reports sound samples are '
                        f'64 bits, but format tage is "{self.tag}", not "3" '
                        f'(floating point). Only 64-bit floating point values '
                        f'are supported for PCM files.')
                encoding = 'PCM_DOUBLE'
            case _:
                raise WAVFileError(f'format chunk reports sound samples are '
                                      f'{self.nbits} bits, but only 8,16,24,32 '\
                                        'and 64 bits are supported')
        self._encoding=encoding
        self._sampledtype = {
            'PCM_U8': "u1",
            'PCM_16': "<i2",
            'PCM_24': "u1",  # more conversion is needed after reading 3 bytes -> int32
            'PCM_32': "<i4",
            'FLOAT': "<f4",
            'DOUBLE': "<f8" }[encoding]
        self._memmap = None

    @property
    def encoding(self):
        return self._encoding

    @property
    def sampledtype(self):
        return self._sampledtype

    @contextmanager
    def _openarray(self):
        with self.open() as br:
            if self._memmap is not None:
                yield self._memmap
            else:
                try:
                    if self._encoding == 'PCM_24':
                        shape = self._datashape + (3,) # byte triplets are sample
                    else:
                        shape = self._datashape
                    self._memmap = np.memmap(filename=br,
                                             mode='r',
                                             shape=shape,
                                             dtype=self._sampledtype,
                                             order='C',
                                             offset=self._audiodataoffset)
                    yield self._memmap
                except Exception:
                    raise
                finally:
                    if hasattr(self._memmap, '_mmap'):
                        self._memmap._mmap.close()  # *may need this for Windows*
                    self._memmap = None

    # FIXME what about origintime?
    def _check_episode(self, *args, startframe=None, endframe=None,
                       starttime=None, endtime=None, **kwargs):

        return check_episode(startframe=startframe, endframe=endframe,
                             starttime=starttime, endtime=endtime,
                             startdatetime=None, enddatetime=None,
                             fs=self._samplingrate, nframes=self._nframes,
                             originstartdatetime=None)

    def __str__(self):
        return (f"<WAVE file '{self.filepath.name}': "
                f"{duration_string(self._nframes / self._samplingrate)}, "
                f"{self._nchannels} channels, {self._encoding}>")

    __repr__ = __str__

    @wraptimeparamsmethod
    def read_frames(self, startframe=None, endframe=None,
                    channelindex=None, out=None, dtype='float64'):
        if channelindex is None:
            channelindex = slice(None)
            nchannels = self._nchannels
        else:
            # TODO look into next avoid advanced indexing if possible?
            channelindex = np.arange(self._nchannels)[channelindex]
            nchannels = len(channelindex)
        with self._openarray() as ar:
            match self._encoding:
                case 'PCM_U8':
                    frames = np.array(ar[startframe:endframe, channelindex],
                              dtype=dtype)
                    return frames * PCMvalue_to_audiofloat_factor['PCM_U8']
                case 'PCM_16':
                    frames = np.array(ar[startframe:endframe, channelindex],
                              dtype=dtype)
                    return frames * PCMvalue_to_audiofloat_factor['PCM_16']
                case 'PCM_24':  # this is read as u1 and shape has extra dim
                    nframes = endframe - startframe
                    out = np.zeros((nframes, nchannels), dtype='<i4')
                    temp = out.view('uint8').reshape(nframes, nchannels, 4)
                    temp[:, :, slice(1,None)] = \
                        ar[startframe:endframe, channelindex].reshape(nframes, nchannels, 3)
                    return out / 0x80000000
                case 'PCM_32':
                    frames = np.array(ar[startframe:endframe, channelindex],
                                      dtype=dtype)
                    return frames * PCMvalue_to_audiofloat_factor['PCM_32']
                case 'FLOAT':
                    return np.array(ar[startframe:endframe, channelindex],
                                    dtype=dtype)
                case 'DOUBLE':
                    return np.array(ar[startframe:endframe, channelindex],
                        dtype=dtype)
