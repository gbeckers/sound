"""
Resource Interchange File Format (RIFF) is a generic file container format for
storing data in tagged chunks. Primarily used for audio and video files.

All chunks have the following format:

    4 bytes: an ASCII identifier for this chunk (examples are "fmt " and
        "data"; note the space in "fmt ").
    4 bytes: an unsigned, little-endian 32-bit integer with the length of this
        chunk (except this field itself and the chunk identifier).
    variable-sized field: the chunk data itself, of the size given in the
        previous field.
    a pad byte, if the chunk's length is not even.

Two chunk identifiers, "RIFF" and "LIST", introduce a chunk that can contain
subchunks. The RIFF and LIST chunk data (appearing after the identifier and
length) have the following format:

    4 bytes: an ASCII identifier for this particular RIFF or LIST chunk (for
        RIFF in the typical case, these 4 bytes describe the content of the
        entire file, such as "AVI " or "WAVE").
    rest of data: subchunks.

The file itself consists of one RIFF chunk, which then can contain further
subchunks: hence, the first four bytes of a correctly formatted RIFF file will
spell out "RIFF".

Source: https://en.wikipedia.org/wiki/Resource_Interchange_File_Format

More info: http://www.tactilemedia.com/info/MCI_Control_Info.html

"""
import contextlib
import struct
import re
import os
import uuid
import warnings
import numpy as np
from contextlib import contextmanager
from pathlib import Path


class RIFFError(Exception):
    def __init__(self, message):
        self.message = message

class RIFFDecode:

    _byteorder = 'little'

    @classmethod
    def _bytestoint(cls, b, unsigned=True):
        """Converts bytes to an integer number"""
        endianness = {'little': '<', 'big': '>'}[cls._byteorder]
        lettercode = {True:  {1: 'B', 2: 'H', 4: 'I', 8: 'Q'},
                      False: {1: 'b', 2: 'h', 4: 'i', 8: 'q'}}[unsigned][len(b)]
        return struct.unpack(f'{endianness}{lettercode}', b)[0]

    @classmethod
    def _bytestostring(cls, b):
        """Converts bytes in a RIFF WAVE file to text"""
        return b.decode('utf-8').rstrip('\x00')

    @classmethod
    def _inttobytes(cls, i, bytesize, unsigned=True):
        """Converts an integer number to bytes"""
        endianness = {'little': '<', 'big': '>'}[cls._byteorder]
        lettercode = {True: {1: 'B', 2: 'H', 4: 'I', 8: 'Q'},
                      False: {1: 'b', 2: 'h', 4: 'i', 8: 'q'}}[unsigned][bytesize]
        return struct.pack(f'{endianness}{lettercode}', i)

class RIFFFile(RIFFDecode):
    """RIFF File

    Header is the first 12 bytes.
    Bytes 0:4 of header should read "RIFF"
    Bytes 4:8 of header specifies the riff body size
    Bytes 8:12 belong to body and specify the form type, e.g. "WAVE"

    """

    _byteorder = 'little' # RIFF file always have bytes in little endian

    def __init__(self, filepath):
        self._filepath = Path(filepath)
        (mode, ino, dev, nlink, uid, gid, filesize, atime, mtime,
         ctime) = os.stat(filepath)
        self._br = None
        with self.open() as br:
            br.seek(0)
            chunkid = br.read(4)
            if chunkid != b'RIFF':
                raise RIFFError(f'File does not seem to be a RIFF file: first f'
                                f'our bytes read "{chunkid}, not "RIFF"')
            bodysize = self._bytestoint(br.read(4), unsigned=True)
            formtype = self._bytestostring(br.read(4))

            if bodysize + 8 != filesize:
                warnings.warn(f"RIFF header body size ({bodysize}) "
                              f"does not match file size ({filesize}), which "
                              f"should normally be {bodysize} + 8 bytes")
        self._filesize = filesize
        self._bodysize = bodysize
        self._formtype = formtype
        self._chunklocations = self._find_chunks()

    @property
    def filepath(self):
        return self._filepath

    @property
    def chunklocations(self):
        return self._chunklocations

    @property
    def formtype(self):
        "RIFF form type"
        return self._formtype

    @property
    def bodysize(self):
        "size in bytes of RIFF body (i.e. RIFF chunk size minus 8 header bytes)"
        return self._bodysize

    @property
    def filesize(self):
        "size in bytes of file"
        return self._filesize

    def __repr__(self):
        return (f'<{self.__class__.__name__}: {self._filepath.name}, '
                f'{self._filesize} bytes, {len(self._chunklocations)} chunks>')

    def _find_chunks(self):
        """finds all chunks in RIFF file"""
        # After RIFF header and format FourCC,
        # child chunks follow starting at byte 12
        bytepos = 12  # first child chunk has to start after form type tag
        chunks = {}
        with self.open() as br:
            while bytepos < self._filesize:
                br.seek(bytepos, 0)
                fourcc = br.read(4).decode('utf-8') # first 4 bytes of child chunk have ID
                chunkid = fourcc.rstrip(' ')
                chunkstart = bytepos
                bodysize = self._bytestoint(br.read(4), unsigned=True)
                chunksize = (8 + bodysize) + (8 + bodysize) % 2  # pad to even position
                if fourcc == "LIST":
                    # first 4 bytes of sub chunk has LIST type ID
                    listid = self._bytestostring(br.read(4))
                    if listid == 'INFO':
                        chunkid = 'LISTINFO'
                chunks[chunkid] = (chunkstart, chunksize)
                bytepos = chunkstart + chunksize
            return chunks

    def _get_bytes(self, startpos, size):
        """Returns file content as bytes.

        Function for low-level access to file content.

        Parameters
        ----------
        startpos: int
          where to start reading (in number of bytes from start of file)
        size: int
          how many bytes to read

        Returns
        -------

        """
        with self.open() as br:
            br.seek(startpos, 0)
            b = br.read(size)
        return b

    def get_chunk(self, chunkid):
        """Get chunk by id
        Will return instance of class with useful specific attributes and methods,
        if chunk type is supported, otherwise an instance of RIFFSubChunk, which
        can be used to inspect contents.

        Parameters
        ----------
        chunkid: str
          chunk id (without any trailing spaces).

        """

        start, size = self._chunklocations[chunkid]
        b = self._get_bytes(start, size)
        match chunkid:
            case 'fmt':
                c = FmtChunk(b)
            case 'bext':
                version = self._bytestoint(b[354:356])
                if version == 0:
                    c = BextChunkV0(b)
                elif version == 1:
                    c = BextChunkV1(b)
                elif version == 2:
                    c = BextChunkV2(b)
                else:
                    raise ValueError(
                        f'Unknown bext chunk version: {version}')
            case 'iXML':
                c = IXMLChunk(b)
            case 'fact':
                c = FactChunk(b)
            case 'LISTINFO':  # has subchunks, we need to know which type it is
                c = LISTINFOChunk(b)
            case 'LIST':
                c = LISTChunk(b)
            case 'olym':
                c = OlymChunk(b)
            case _:
                c = RIFFSubChunk(b)
        return c

    @contextmanager
    def open(self):
        with open(self._filepath, 'rb') as br:
            self._br = br
            yield br
        self._br = None

class RIFFSubChunk(RIFFDecode):
    """
    bytes 0-8 are header, 8: is body
    bytes 0:4 are id
    bytes 4:8 are body size
    """

    def __init__(self, b):
        """

        Parameters
        ----------
        b: bytes

        """
        if not isinstance(b, bytes | bytearray):
            raise TypeError('b must be a bytes object')
        self._bytes = bytearray(b)
        self._chunkid = self._bytestostring(b[:4])
        self._chunksize = len(b)
        self._chunkbodysize = self._bytestoint(b[4:8], unsigned=True)

    @property
    def bytes(self):
        return self._bytes

    @property
    def chunkid(self):
        """Four character string (FourCC) indicating type of RIFF chunk"""
        return self._chunkid

    @property
    def chunksize(self):
        """Length of RIFF chunk in bytes"""
        return self._chunksize

    @property
    def chunkbodysize(self):
        """Length of RIFF chunk body (i.e. without id and size field ) in bytes"""
        return self._chunkbodysize

    @property
    def chunkbody(self):
        return self._bytes[8:]

    def __repr__(self):
        return (f'<RIFF chunk "{self._chunkid}": {self.chunksize} bytes>')


class MetaDataChunk(RIFFSubChunk):
    """A RIFF subchunk with defined data fields, e.g. 'fmt ' chunk

    """

    def __init__(self, b):
        RIFFSubChunk.__init__(self, b)
        self._fields = {} # populated by children

    @property
    def fields(self):
        return self._fields

    def _get_bytesasint(self, field):
        start, size = self._fields[field]
        return self._bytestoint(self._bytes[start:start + size])

    def _get_bytesasstring(self, field):
        start, size = self._fields[field]
        return self._bytestostring(self._bytes[start:start + size])

    def _get_bytes(self, field):
        start, size = self._fields[field]
        return self._bytes[start:start + size]

    def _set_stringasbytes(self, field, s):
        start, size = self._fields[field]
        b = bytearray(size)
        s = s.encode('utf-8')
        b[0:len(s)] = s
        self._bytes[start:start + size] = b

    def _set_intasbytes(self, field, i):
        start, size = self._fields[field]
        self._bytes[start:start + size] = self._inttobytes(i, size)

    def to_dict(self):
        d = {}
        for field in self._fields.keys():
            d[field] = getattr(self, field)
        return d

    def __str__(self):
        s = f'{self.__repr__()}\n'
        for p in self.fields:
            s = f'{s}  {p}: {getattr(self, p)}\n'
        return s


class FmtChunk(MetaDataChunk):
    """WAVE Format chunk

    """

    def __init__(self, b):
        MetaDataChunk.__init__(self, b)
        if not self.chunkid == 'fmt ':
            raise RIFFError(f'{self.chunkid} is not a "fmt " RIFF chunk')
        self._fields.update({
            'tag': (8, 2),
            'nchannels': (10, 2),
            'samplingrate': (12, 4),
            'avgbytespersecond': (16, 4),
            'blocksize': (20, 2),
            'nbits': (22, 2)
        })
        if len(self.bytes) > 24: # extension present
            self._fields.update({
                'extensionsize': (24,2),
                'extensionfirstfield': (26, 2),
                'channelmask': (28, 4),
                'subformatGUID': (32, 16)
            })

    @property
    def tag(self):
        return self._get_bytesasint('tag')

    @property
    def nchannels(self):
        return self._get_bytesasint('nchannels')

    @property
    def samplingrate(self):
        return self._get_bytesasint('samplingrate')

    @property
    def avgbytespersecond(self):
        return self._get_bytesasint('avgbytespersecond')

    @property
    def blocksize(self):
        return self._get_bytesasint('blocksize')

    @property
    def nbits(self):
        return self._get_bytesasint('nbits')

    @property
    def extensionsize(self):
        if 'extensionsize' in self._fields:
            return self._get_bytesasint('extensionsize')
        else:
            return None

    @property
    def extensionfirstfield(self):
        if 'extensionfirstfield' in self._fields:
            return self._get_bytesasint('extensionfirstfield')
        else:
            return None

    @property
    def channelmask(self):
        if 'channelmask' in self._fields:
            return self._get_bytes('channelmask')
        else:
            return None

    @property
    def subformatGUID(self):
        if 'subformatGUID' in self._fields:
            return self._get_bytes('subformatGUID')
        else:
            return None

    def __repr__(self):
        return (f'<WAVE "fmt " chunk: {self.chunksize} bytes>')


class BextChunkV0(MetaDataChunk):
    """BWF Broadcast Audio Extension Chunk, version 0

    see: https://tech.ebu.ch/docs/tech/tech3285.pdf
    see: https://www.digitizationguidelines.gov/guidelines/digitize-embedding.html

    bext chunk contains metadata on recording. It is relatively well-supported,
    and used by at least some field recorders (e.g. Sound Devices 7-series
    recorders).

    """

    def __init__(self, b):
        MetaDataChunk.__init__(self, b)
        self._fields = {
            'Description': (8, 256),
            'Originator': (264, 32),
            'OriginatorReference': (296, 32),
            'OriginationDate': (328, 10),
            'OriginationTime': (338, 8),
            'TimeReference': (346, 8),
            'Version': (354, 2),
            'Reserved': (356, 254),
            'CodingHistory': (610, len(b) - 610),
        }


    @property
    def Description(self):
        """ASCII string (maximum 256 characters) containing a free description
        of the sequence. To help applications which only display a short
        description, it is recommended that a résumé of the description is
        contained in the first 64 characters (padded with Nulls), and the last
        192 characters are used for details.

        """
        return self._get_bytesasstring('Description')

    @Description.setter
    def Description(self, s):
        self._set_stringasbytes('Description', s)

    @property
    def Originator(self):
        """ASCII string (maximum 32 characters) containing the name of the
        originator/producer of the audio file."""
        return self._get_bytesasstring('Originator')

    @Originator.setter
    def Originator(self, s):
        self._set_stringasbytes('Originator', s)

    @property
    def OriginatorReference(self):
        """ASCII string (maximum 32 characters) containing a non-ambiguous
        reference allocated by the originating organization."""
        return self._get_bytesasstring('OriginatorReference')

    @OriginatorReference.setter
    def OriginatorReference(self, s):
        self._set_stringasbytes('OriginatorReference', s)

    @property
    def OriginationDate(self):
        """Ten ASCII characters containing the date of creation of the audio
        sequence. This is understood to mean the local date in the timezone for
        the archival entity. Format is ISO 8601, e.g. "YYYY-MM-DD" or a year
        range, e.g. "2023/2025" or "2023--2025". """
        return self._get_bytesasstring('OriginationDate')

    @OriginationDate.setter
    def OriginationDate(self, date):
        # ISO 8601
        try:
            date = str(np.datetime64(date))
        except:
            if not re.search('^[0-9]{4}(\/|--)[0-9]{4}$', date):
                raise ValueError(f'Invalid date: {date}. Valid examples are: '
                                 f'2024-07-18, 2024-07, 2024, or year ranges '
                                 f'like 2023/2024 or 2023--2024.')
        self._set_stringasbytes('OriginationDate', date)

    @property
    def OriginationTime(self):
        """Eight ASCII characters containing the time of creation of the audio
        sequence. This is understood to mean the local time in the timezone for
        the archival entity. Format is ISO 8601 "HH:MM:SS", "HH:MM", or "HH"."""
        return self._get_bytesasstring('OriginationTime')

    @OriginationTime.setter
    def OriginationTime(self, time):
        # ISO 8601
        if not re.search('^[0-2][0-9](:[0-5][0-9]){,2}$', time):
            raise ValueError(f'Invalid time: {time}')
        self._set_stringasbytes('OriginationTime', time)

    @property
    def TimeReference(self):
        """Timecode of the sequence. It is a 64-bit value which contains the
        first sample count since midnight. The number of samples per second
        depends on the sampling frequency."""
        return self._get_bytesasint('TimeReference')

    @TimeReference.setter
    def TimeReference(self, timeref):
        self._set_intasbytes('TimeReference', timeref)

    @property
    def Version(self):
        """An unsigned binary number giving the version of the BWF. The number
        is particularly relevant for the carriage of the UMID and loudness
        information"""
        return self._get_bytesasint('Version')

    @Version.setter
    def Version(self, version):
        self._set_intasbytes(self, 'Version', version)

    @property
    def Reserved(self):
        """254 bytes reserved for extensions."""
        return self.bytes[356:610].rstrip(b'\x00')

    @property
    def CodingHistory(self):
        """Non-restricted ASCII characters, containing a collection of strings
        terminated by CR/LF. Each string contains a description of a coding
        process applied to the audio data. Each new coding application is
        required to add a new string with the appropriate information. This
        information must contain the type of sound (PCM or MPEG) with its
        specific parameters: PCM: mode (mono, stereo), size of the sample
        (8, 16 bits) and sample frequency: MPEG : sample frequency, bit-rate,
        layer (I or II) and the mode (mono, stereo, joint stereo or dual
        channel). It is recommended that the manufacturers of the coders
        provide an ASCII string for use in the coding history."""
        return self._get_bytesasstring('CodingHistory')

    @CodingHistory.setter
    def CodingHistory(self, s):
        self._set_stringasbytes('CodingHistory', s)

    def __repr__(self):
        return (f'<BWF "bext" chunk: {self.chunksize} bytes>')

    def __str__(self):
        s = f'{self.__repr__()}\n'
        regex = re.compile("\r\n")
        repl = "\n    "
        for field, (start,size) in self._fields.items():
            val = getattr(self, field)
            if isinstance(val, str):
                val = regex.sub(repl, val)
                if '\n' in val:
                    val = f"{repl}'{val}"
                else:
                    val = f"'{val}"
                s = f"{s}{field}: " + val.rstrip(repl) + "'\n"
            else:
                s = f'{s}{field}: {val}\n'
        return s



class BextChunkV1(BextChunkV0):
    """BWF Broadcast Audio Extension Chunk, version 1

    see: https://tech.ebu.ch/docs/tech/tech3285.pdf
    see: https://www.digitizationguidelines.gov/guidelines/digitize-embedding.html

    bext chunk contains metadata on recording. It is relatively well-supported,
    and used by at least some field recorders (e.g. Sound Devices 7-series
    recorders).

    Version 1 differs from Version 0 only in that 64 of the 254 Reserved bytes
    in Version 0 are used to contain a SMPTE UMID.

    """

    def __init__(self, b):
        BextChunkV0.__init__(self, b)
        self._fields.update({
            'UMID': (356, 64),
            'Reserved': (420, 190),
        })

    @property
    def UMID(self):
        """UMID 64 bytes containing a UMID (Unique Material Identifier) to the
        SPMTE 330M standard. If only a 32 byte basic UMID is used, the last 32
        bytes should be set to zero. """
        return self.bytes[356:420].rstrip(b'\x00')

    # def __str__(self):
    #     s = super().__str__()
    #     s = f'{s}  UMID: {self.UMID}\n'
    #     return s



class BextChunkV2(BextChunkV1):
    """BWF Broadcast Audio Extension Chunk, version 1

    see: https://tech.ebu.ch/docs/tech/tech3285.pdf
    see: https://www.digitizationguidelines.gov/guidelines/digitize-embedding.html

    bext chunk contains metadata on recording. It is relatively well-supported,
    and used by at least some field recorders (e.g. Sound Devices 7-series
    recorders).

    Version 2 is a substantial revision of Version 1 which incorporates
    loudness metadata (in accordance with EBU R 128 [2]) and which takes
    account of the publication of Supplements 1 – 6 and other relevant
    documentation. This version is fully compatible with Versions 0 and 1, but
    users who wish to ensure that their files meet the requirements of EBU
    Recommendation R 128 will need to ensure that their systems can read and
    write the loudness metadata.

    """

    def __init__(self, b):
        BextChunkV1.__init__(self, b)
        self._fields.update({
            'LoudnessValue': (420, 2),
            'LoudnessRange': (422, 2),
            'MaxTruePeakLevel': (424, 2),
            'MaxMomentaryLoudness': (426, 2),
            'MaxShortTermLoudness': (428, 2),
            'Reserved': (430, 180)
        })

    @property
    def LoudnessValue(self):
        """A 16-bit signed integer, equal to round (100x the Inegrated Loudness
        Value of the file in LUFS). (Established in version 2.)"""
        return self._get_bytesasint('LoudnessValue')

    @LoudnessValue.setter
    def LoudnessValue(self, value):
        self._set_intasbytes(self, 'LoudnessValue', value)

    @property
    def LoudnessRange(self):
        """A 16-bit signed integer, equal to round (100x the Integrated
        Loudness Range of the file in LU). (Established in version 2.)"""
        return self._get_bytesasint('LoudnessRange')

    @LoudnessRange.setter
    def LoudnessRange(self, value):
        self._set_intasbytes(self, 'LoudnessRange', value)

    @property
    def MaxTruePeakLevel(self):
        """A 16-bit signed integer, equal to round (100x the Maximum True Peak
        Value of the file in dBTP). (Established in version 2.)"""
        return self._get_bytesasint('MaxTruePeakLevel')

    @MaxTruePeakLevel.setter
    def MaxTruePeakLevel(self, value):
        self._set_intasbytes(self, 'MaxTruePeakLevel', value)

    @property
    def MaxMomentaryLoudness(self):
        """A 16-bit signed integer, equal to round (100x the highest value of
        the Momentary Loudness Level of the file in LUFS). (Established in
        version 2.)"""
        return self._get_bytesasint('MaxMomentaryLoudness')

    @MaxMomentaryLoudness.setter
    def MaxMomentaryLoudness(self, value):
        self._set_intasbytes(self, 'MaxMomentaryLoudness', value)

    @property
    def MaxShortTermLoudness(self):
        """A 16-bit signed integer, equal to round (100x the highest value of
        the Short-term Loudness Level of the file in LUFS). (Established in
        version 2.)"""
        return self._get_bytesasint('MaxShortTermLoudness')

    @MaxShortTermLoudness.setter
    def MaxShortTermLoudness(self, value):
        self._set_intasbytes(self, 'MaxShortTermLoudness', value)


class IXMLChunk(MetaDataChunk):
    """RIFF iXML chunk

    http://www.gallery.co.uk/ixml/

    """

    def __init__(self, b):
        MetaDataChunk.__init__(self, b)
        if not self.chunkid == 'iXML':
            raise RIFFError(f'{self.chunkid} is not an "iXML" chunk')

        self._fields.update({
            'xmlstr': (8, len(b)-8)
        })

    @property
    def xmlstr(self):
        """The complete iXML text, including xlm version and encoding
        tags."""
        return self._get_bytesasstring('xmlstr')


    def __repr__(self):
        return (f'<WAV "iXML" chunk: {self.chunksize} bytes>')

    def __str__(self):
        s = f'{self.__repr__()}\n'
        regex = re.compile("\r\n")
        repl = "\n    "
        val = regex.sub(repl, self.xmlstr)
        if '\n' in val:
            val = f"{repl}{val}"
        else:
            val = f"'{val}"
        s = f"{s}{val.rstrip(repl)}" + "\n"
        return s

class FactChunk(MetaDataChunk):
    """RIFF fact chunk

    First four bytes of body contain number of frames. May contain
    additional data.

    """

    def __init__(self, b):
        MetaDataChunk.__init__(self, b)
        if not self.chunkid == 'fact':
            raise RIFFError(f'{self.chunkid} is not a fact chunk')
        self._fields.update({
            'nframes': (8,4),
        })

    @property
    def nframes(self):
        return self._get_bytesasint('nframes')

    def __repr__(self):
        return (f'<WAVE "fact" chunk: {self._chunksize} bytes>')


class OlymChunk(MetaDataChunk):
    """RIFF olym chunk

    This information is found in WAV files from Olympus PCM linear recorders
    like the LS-5, LS-10, LS-11.

    Note complete whatsoever. Found some info at
    https://exiftool.org/TagNames/Olympus.html#WAV

    """

    def __init__(self, b):
        MetaDataChunk.__init__(self, b)
        if not self.chunkid == 'olym':
            raise RIFFError(f'{self.chunkid} is not an "olym" chunk')

        self._fields.update({
            'Model': (20, 14),
            'FileNumber': (36, 4),
            'DateTimeOriginal': (46, 12),
            'DateTimeEnd': (58, 12),
            'RecordingTime': (70, 6),
            'Duration': (520, 4)
        })

    @property
    def Model(self):
        return self._get_bytesasstring('Model')

    @property
    def FileNumber(self):
        return self._get_bytesasint('FileNumber')

    @property
    def DateTimeOriginal(self):
        return self._get_bytesasstring('DateTimeOriginal')

    @property
    def DateTimeEnd(self):
        return self._get_bytesasstring('DateTimeEnd')

    @property
    def RecordingTime(self):
        return self._get_bytesasstring('RecordingTime')

    @property
    def Duration(self):
        """Duration in milliseconds."""
        return self._get_bytesasint('Duration')

    def __repr__(self):
        return (f'<WAVE "olym" chunk: {self.chunksize} bytes>')

class LISTChunk(MetaDataChunk):

    def __init__(self, b):
        MetaDataChunk.__init__(self, b)
        if not self.chunkid == 'LIST':
            raise RIFFError(f'{self.chunkid} is not a "LIST" chunk')
        self._type = self.bytes[8:12].decode('utf-8')

    @property
    def type(self):
        """LIST type, e.g. INFO """
        return self._type

    def __repr__(self):
        return (f'<WAVE "LIST" chunk, type "{self._type}": {self.chunksize} bytes>')


# TODO change/add/remove fields
class LISTINFOChunk(LISTChunk):
    """

    Common INFO IDs:

    IARL 	The location where the subject of the file is archived
    INAM 	Title of the subject of the file (name)
    ICMT 	General comments about the file or its subject
    ICRD 	The date the subject of the file was created (creation date) (e.g., "2022-12-31")
    ICOP 	Copyright information about the file (e.g., "Copyright Some Company 2011")

    Less common INFO IDs:

    IART 	The artist of the original subject of the file
    ICMS 	The name of the person or organization that commissioned the original subject of the file
    IENG 	The name of the engineer who worked on the file
    IGNR 	The genre of the subject
    IKEY 	A list of keywords for the file or its subject
    IMED 	Medium for the original subject of the file
    IPRD 	Name of the title the subject was originally intended for
    ISBJ 	Description of the contents of the file (subject)
    ISFT 	Name of the software package used to create the file
    ISRC 	The name of the person or organization that supplied the original subject of the file
    ISRF 	The original form of the material that was digitized (source form)
    ITCH 	The name of the technician who digitized the subject file

    """

    def __init__(self, b):
        LISTChunk.__init__(self, b)
        if not self._type == 'INFO':
            raise RIFFError(f'{self.chunkid} is a "LIST" chunk, but not of '
                             f'"INFO" subtype ({self._type})')
        bytepos = 12
        self._fields = {}
        while bytepos < len(b):
            infoid = self.bytes[bytepos:bytepos+4].decode('utf-8')
            infosize = self._bytestoint(self.bytes[bytepos+4:bytepos+8])
            self._fields[infoid] = (bytepos + 8, infosize)
            bytepos += 8 + infosize

    def __getattr__(self, item):
        if item in self._fields:
            return self._get_bytesasstring(item)
        else:
            return getattr(self, item)
