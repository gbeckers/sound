"""AudioFile makes audio files accessible though one interface. Under the hood reading data can be implemented natively
(currently for WAVE format with PCM encoding) or by different other libraries (currentlu soundfile/libsndfile for the rest).

"""
import os
import numpy as np
from datetime import datetime
from pathlib import Path
from .utils import duration_string, write_jsonfile
from .check_arg import check_arg
from .wavpcmfile import WAVEFileAudioReader, WAVFileError
from .libsndfile import LibSndFileReader, LibSndFileError

defaultaudioformat = 'WAV'
defaultaudioencoding = 'FLOAT'

class AudioFileError(Exception):
    def __init__(self, message):
        self.message = message

class UnsupportedAudioFileError(AudioFileError):

    def __init__(self, message):
        self.message = message


class AudioFile:
    """"""

    _classid = 'AudioFile'

    def __init__(self, filepath):
        self._filepath = Path(filepath)
        (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(
            self._filepath)
        self._filesize = size

        try:
            datareader = WAVEFileAudioReader(filepath=filepath)
        except WAVFileError as e:
            try:
                import soundfile
            except ImportError:
                    pass
            from .libsndfile import LibSndFileReader
            try:
                datareader =  LibSndFileReader(filepath=filepath)
            except LibSndFileError as e:
                raise e
        self._datareader = datareader
        self._sizeinbytes = size
        self._nframes = check_arg(datareader.nframes, 'nframes')
        self._nchannels = check_arg(datareader.nchannels, 'nchannels')
        self._samplingrate = check_arg(datareader.samplingrate, 'samplingrate') # fs as specified in file (may be different from SndFile)
        self._fileformat = datareader.fileformat
        self._encoding = datareader.encoding
        self.open = datareader.open
        self.read_frames = datareader.read_frames


    @property
    def filepath(self):
        "path of audiofile"
        return self._filepath

    @property
    def sizeinbytes(self):
        return self._sizeinbytes

    @property
    def nframes(self):
        "number of audio frames (time samples)"
        return self._nframes

    @property
    def nchannels(self):
        "number of audio channels"
        return self._nchannels

    @property
    def samplingrate(self):
        "sampling rate"
        return self._samplingrate

    @property
    def dt(self):
        return 1 / self._samplingrate

    @property
    def duration(self):
        "duration of audio in seconds"
        return self._nframes / self._samplingrate

    @property
    def fileformat(self):
        "data format of audio file"
        return self._fileformat

    @property
    def encoding(self):
        "audio encoding type"
        return self._encoding

    @property
    def metadata(self):
        return self._datareader.metadata

    def __str__(self):
        return (f"<AudioFile '{self.filepath.name}': "
                f"{duration_string(self._nframes / self._samplingrate)}, "
                f"{self._nchannels} channels>")

    __repr__ = __str__

    def datetimeinfo(self):
        l = []
        (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(
            self._filepath)
        # we start with most unreliable
        startdatetime = np.datetime64(datetime.fromtimestamp(mtime), 's')
        l.append(('file last modification', str(startdatetime)))

        if 'olym' in self.metadata: #
            ts = self.metadata['olym'].DateTimeOriginal
            startdatetime = np.datetime64(f'20{ts[0:2]}-{ts[2:4]}-{ts[4:6]}T{ts[6:8]}:{ts[8:10]}:{ts[10:12]}', 's')
            l.append(('olympus RIFF info "DateTimeOriginal"', str(startdatetime)))
        if 'bext' in self.metadata:
            bext = self.metadata['bext']
            od = bext.OriginationDate
            ot = bext.OriginationTime
            if od != '':
                if ot != '':
                    startdatetime = np.datetime64(f'{od}T{ot}', 's')
                else:
                    startdatetime = np.datetime64(od, 'D')
                l.append(('bext RIFF info', str(startdatetime)))
        return tuple(l)

    def to_sndfile(self, path=None, startdatetime=None, origintime=0.0,
                   samplingrate=None, scalingfactor=None, unit=None,
                   usermetadata=None, overwrite=False):
        from .sndfile import SndFile
        if path is None:
            path = self.filepath.with_suffix('.sound')
        else:
            path = Path(path)
            if path.is_dir():
                path = path / self.filepath.with_suffix('.sound').name
        audiofilepath = self.filepath.relative_to(path, walk_up=True)
        d = {'sndinfo':
                {'audiofilepath': audiofilepath,
                 'nframes': self._nframes,
                 'nchannels': self._nchannels}
             }
        smd = d['sndmetadata'] = {'samplingrate': self._samplingrate}
        if origintime is not None:
            smd.update({'origintime': float(origintime)})
        if samplingrate is not None:
            smd.update({'samplingrate': samplingrate})
        if scalingfactor is not None:
            smd.update({'scalingfactor': scalingfactor})
        if unit is not None:
            smd.update({'unit': unit})
        rmd = d['recordingdata'] = {}
        if startdatetime is not None:
            rmd.update({'startdatetime': np.datetime64(startdatetime)})
        if usermetadata is not None:
            d.update({'usermetadata': usermetadata})
        write_jsonfile(path=path, data=d, overwrite=overwrite)
        s = SndFile(path=path)
        d = s._saveparams
        write_jsonfile(path=path, data=d, overwrite=overwrite)
        return SndFile(path=path)








