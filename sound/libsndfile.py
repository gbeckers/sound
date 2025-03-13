"""All code regarding the soundfile/libsndfile library goes in this module.
These libraries are not a hard requirement and are optionally installed.

"""

import soundfile as sf
from pathlib import Path
from contextlib import contextmanager, ExitStack

##################################

# most are supported via the soundfile library
# non-compressed WAVE files (including BWF ) are handled directly by sound
supported_fileformats = {
    'AIFF': 'AIFF (Apple/SGI)',
    'AU': 'AU (Sun/NeXT)',
    'AVR': 'AVR (Audio Visual Research)',
    'CAF': 'CAF (Apple Core Audio File)',
    'FLAC': 'FLAC (Free Lossless Audio Codec)',
    'HTK': 'HTK (HMM Tool Kit)',
    'SVX': 'IFF (Amiga IFF/SVX8/SV16)',
    'MAT4': 'MAT4 (GNU Octave 2.0 / Matlab 4.2)',
    'MAT5': 'MAT5 (GNU Octave 2.1 / Matlab 5.0)',
    'MPC2K': 'MPC (Akai MPC 2k)',
    'MP3': 'MPEG-1/2 Audio',
    'OGG': 'OGG (OGG Container format)',
    'PAF': 'PAF (Ensoniq PARIS)',
    'PVF': 'PVF (Portable Voice Format)',
    'RAW': 'RAW (header-less)',
    'RF64': 'RF64 (RIFF 64)',
    'SD2': 'SD2 (Sound Designer II)',
    'SDS': 'SDS (Midi Sample Dump Standard)',
    'IRCAM': 'SF (Berkeley/IRCAM/CARL)',
    'VOC': 'VOC (Creative Labs)',
    'W64': 'W64 (SoundFoundry WAVE 64)',
    'WAV': 'WAV (Microsoft)',
    'NIST': 'WAV (NIST Sphere)',
    'WAVEX': 'WAVEX (Microsoft)',
    'WVE': 'WVE (Psion Series 3)',
    'XI': 'XI (FastTracker 2)'
}

# we follow terminology from soundfile library, except that FLOAT and DOUBLE
# are now PCM_FLOAT and PCM_DOUBLE for clarity and consistency
supported_encodings = {
    'PCM_S8': 'Signed 8 bit PCM',
    'PCM_16': 'Signed 16 bit PCM',
    'PCM_24': 'Signed 24 bit PCM',
    'PCM_32': 'Signed 32 bit PCM',
    'PCM_U8': 'Unsigned 8 bit PCM',
    'PCM_FLOAT': '32 bit float',
    'PCM_DOUBLE': '64 bit float',
    'ULAW': 'U-Law',
    'ALAW': 'A-Law',
    'IMA_ADPCM': 'IMA ADPCM',
    'MS_ADPCM': 'Microsoft ADPCM',
    'GSM610': 'GSM 6.10',
    'G721_32': '32kbs G721 ADPCM',
    'G723_24': '24kbs G723 ADPCM',
    'G723_40': '40kbs G723 ADPCM',
    'DWVW_12': '12 bit DWVW',
    'DWVW_16': '16 bit DWVW',
    'DWVW_24': '24 bit DWVW',
    'VOX_ADPCM': 'VOX ADPCM',
    'NMS_ADPCM_16': '16kbs NMS ADPCM',
    'NMS_ADPCM_24': '24kbs NMS ADPCM',
    'NMS_ADPCM_32': '32kbs NMS ADPCM',
    'DPCM_16': '16 bit DPCM',
    'DPCM_8': '8 bit DPCM',
    'VORBIS': 'Vorbis',
    'OPUS': 'Opus',
    'MPEG_LAYER_I': 'MPEG Layer I',
    'MPEG_LAYER_II': 'MPEG Layer II',
    'MPEG_LAYER_III': 'MPEG Layer III',
    'ALAC_16': '16 bit ALAC',
    'ALAC_20': '20 bit ALAC',
    'ALAC_24': '24 bit ALAC',
    'ALAC_32': '32 bit ALAC'
}





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

class LibSndFileError(Exception):
    def __init__(self, message):
        self.message = message

class LibSndFileReader:
    """Audio file that is read using the lbsndfile library, via python's
    soundfile library

    """

    def __init__(self, filepath):
        filepath = Path(filepath)
        (nframes, nchannels, fs, fileformat, encoding,
         endianness, extrainfo) = self.get_info(filepath)
        self._filepath = filepath
        self._nframes = nframes
        self._nchannels = nchannels
        self._samplingrate = fs
        self._fileformat = fileformat
        self._encoding = encoding
        self._endianness = endianness
        self._extrainfo = extrainfo
        self._fileobj = None

    @property
    def filepath(self):
        return self._filepath

    @property
    def nframes(self):
        return self._nframes

    @property
    def nchannels(self):
        return self._nchannels

    @property
    def samplingrate(self):
        return self._samplingrate

    @property
    def fileformat(self):
        return self._fileformat

    @property
    def encoding(self):
        return self._encoding

    @property
    def endianness(self):
        return self._endianness

    @property
    def metadata(self):
        return {'extrainfo': self._extrainfo}

    def get_info(self, audiofilepath):

        with sf.SoundFile(str(audiofilepath)) as f:
            nframes = len(f)
            nchannels = f.channels
            fs = f.samplerate
            fileformat = f.format
            encoding =  f.subtype
            endianness = f.endian
            extrainfo = f.extra_info
        return (nframes, nchannels, fs, fileformat, encoding, endianness,
                extrainfo)

    @contextmanager
    def _openfile(self):
        if self._fileobj is not None:
            yield self._fileobj
        else:
            try:
                with sf.SoundFile(str(self._filepath),
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
                          f'{startframe} in {self._filepath}')
                    raise
            try:
                frames = af.read(endframe - startframe, dtype=dtype,
                                 always_2d=True, out=out)
            except:
                # TODO create a proper error
                print(f'Unexpected error when reading {endframe - startframe} '
                      f'frames, starting from frame {startframe} in '
                      f'{self._filepath}')
                raise
        if channelindex is not None:
            frames = frames[:, channelindex]
        return frames


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