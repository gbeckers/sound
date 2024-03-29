import numpy as np
from contextlib import contextmanager
from pathlib import Path
from darr import asarray

from .sndinfo import SndInfo, _create_sndinfo

from .utils import duration_string, check_episode, iter_timewindowindices, \
    wraptimeparamsmethod, calcsecstonexthour, peek_iterable
from ._version import get_versions

__all__ = ['Snd']

def _check_frames(frames):
    requiredattrs = ('dtype', 'shape')
    if not all(hasattr(frames, attr) for attr in requiredattrs):
        raise TypeError(f"`frames` object does not have all of the required attributes: {requiredattrs} ")
    return frames

def _check_origintime(origintime):
    return float(origintime)

def _check_startdatetime(startdatetime):
    return np.datetime64(startdatetime)

def _check_fs(fs):
    return fs

def _check_scalingfactor(scalingfactor):
    return scalingfactor

def _check_unit(unit):
    return unit

def _check_metadata(metadata):
    return metadata

class BaseSnd:
    _timeaxis = 0
    _channelaxis = 1
    _classid = 'BaseSnd'
    _classdescr = 'represents a continuous sound'
    _version = get_versions()['version']

    """A base class for continuous sounds.
    
    To be subclassed to be useful. Subclasses need to implement a `read_frames` method that 
    retrieves the actual sound frame data. They can also implement an `open` method if useful. 
    
    Parameters
    ----------
    frames: array-like
      Time on first axis, channel on second axis. Needs to support indexing, to have `dtype`and `shape` attributes,
      and to implement an `open` method.
    fs: {int, float}
      Sampling rate in Hz.
    dtype: numpy dtype
        This is the dtype of the raw frame values when they are read internally.
    startdatetime: str
      The date and time when the sound started to occur. The most basic way to create a datetime is from strings in 
      ISO 8601 date or datetime format. The unit for internal storage is automatically selected from the form of the 
      string, and can be either a date unit or a time unit. The date units are years (‘Y’), months (‘M’), weeks (‘W’), 
      and days (‘D’), while the time units are hours (‘h’), minutes (‘m’), seconds (‘s’), milliseconds (‘ms’), and 
      some additional SI-prefix seconds-based units. This parameter also accepts the string “NAT”, in any combination 
      of lowercase/uppercase letters, for a “Not A Time” value.
      
    """

    def __init__(self, nframes, nchannels, fs, framedtype=None, scalingfactor=None,
                 encoding=None, startdatetime='NaT', origintime=0.0, unit=None,
                 metadata=None, setparamcallback=None):

        self._nframes = nframes
        self._nchannels = nchannels
        self._framedtype = framedtype
        if not isinstance(fs, (int, float)):
            raise TypeError(f"`fs` can only be an int or float, not; {type(fs)}")
        self._fs = _check_fs(fs)
        # self._dtype = dtype
        self._scalingfactor = _check_scalingfactor (scalingfactor)
        self._encoding = encoding
        self._startdatetime = _check_startdatetime(startdatetime)
        self._origintime = _check_origintime(origintime)
        self._unit = _check_unit(unit)
        if metadata is None:
            metadata = {}
        self._metadata = _check_metadata(metadata)
        self._setparamcallback = setparamcallback  # for subclasses

    @property
    def nframes(self):
        """Number of time frames (1 frame can have multiple channels)."""
        return self._nframes

    @property
    def nchannels(self):
        """Number of channels."""
        return self._nchannels

    @property
    def framedtype(self):
        """NumPy dtype of the frames as returned by the `read_frames` method"""
        return self._framedtype

    @property
    def fs(self):
        """Sampling rate in Hz."""
        return self._fs

    @property
    def dt(self):
        """Sampling period in seconds."""
        return 1 / self._fs

    # @property
    # def dtype(self):
    #     """Numeric data type of frames (numpy dtype)."""
    #     return self._dtype

    @property
    def scalingfactor(self):
        """Multiplication factor to apply to frames when read from source."""
        return self._scalingfactor

    @property
    def encoding(self):
        """The encoding type from which the frames have been read."""
        return self._encoding

    @property
    def duration(self):
        return self._nframes / self._fs

    @property
    def startdatetime(self):
        return self._startdatetime

    @property
    def origintime(self):
        return self._origintime

    @property
    def enddatetime(self):
        return self.frameindex_to_datetime(self._nframes, where='end')

    @property
    def startepochtime(self):
        if str(self.startdatetime) == "NaT":
            return None
        else:
            return (np.datetime64(self.startdatetime) -
                    np.datetime64('1970-01-01T00:00:00')) / \
                   np.timedelta64(1, 's')

    @property
    def endepochtime(self):
        if str(self.startdatetime) == "NaT":
            return None
        else:
            return self.startepochtime + self.duration

    @property
    def unit(self):
        """The unit of the sound signal"""
        return self._unit

    @property
    def metadata(self):
        """Returns *copy* of metadata dict. Use `set_metadata` method if you
        want to change metadata."""
        return self._metadata.copy()

    def set_fs(self, fs):
        fs = _check_fs(fs)
        if self._setparamcallback is not None:
            self._setparamcallback('fs', fs, self._saveparams)
        self._fs = fs

    def set_metadata(self, metadata):
        metadata = _check_metadata(metadata)
        if self._setparamcallback is not None:
            self._setparamcallback('metadata', metadata, self._saveparams)
        self._metadata = metadata

    def set_origintime(self, origintime):
        origintime = _check_origintime(origintime)
        if self._setparamcallback is not None:
            self._setparamcallback('origintime', origintime, self._saveparams)
        self._origintime = origintime

    def set_scalingfactor(self, scalingfactor):
        scalingfactor = _check_scalingfactor(scalingfactor)
        if self._setparamcallback is not None:
            self._setparamcallback('scalingfactor', scalingfactor, self._saveparams)
        self._scalingfactor = scalingfactor

    def set_startdatetime(self, startdatetime):
        startdatetime = _check_startdatetime(startdatetime)
        if self._setparamcallback is not None:
            self._setparamcallback('startdatetime', startdatetime, self._saveparams)
        self._startdatetime = startdatetime

    def set_unit(self, unit):
        unit = _check_unit(unit)
        if self._setparamcallback is not None:
            self._setparamcallback('unit', unit)
        self._unit = unit

    def __str__(self):
        totdur = duration_string(self._nframes * self.dt)
        if self._nchannels == 1:
            chstr = "channel"
        else:
            chstr = "channels"
        return f'{self._classid} <{totdur}, {self._fs} Hz, {self._nchannels} {chstr}>'

    __repr__ = __str__

    def __eq__(self, other):
        if not self.fs == other.fs:
            return False
        if not self.origintime == other.origintime:
            return False
        if not str(self.startdatetime) == str(other.startdatetime):
            return False
        if not self.nchannels == other.nchannels:
            return False
        if not self.nframes == other.nframes:
            return False
        if not self.scalingfactor == other.scalingfactor:
            return False
        if not self.unit == other.unit:
            return False
        blocklen = int(self.fs)
        for i,j in zip(self.iterread_frames(blocklen=blocklen),
                       other.iterread_frames(blocklen=blocklen)):
            if not (i==j).all():
                return False
        return True

    def seek_differences(self, other):
        d = {}
        if not self.fs == other.fs:
            d['fs'] = (self.fs, other.fs)
        if not self.origintime == other.origintime:
            d['origintime'] = (self.origintime, other.origintime)
        if not str(self.startdatetime) == str(other.startdatetime):
            d['startdatetime'] = (str(self.startdatetime),
                                  str(other.startdatetime))
        if not self.nchannels == other.nchannels:
            d['nchannels'] = (self.nchannels, other.nchannels)
        if not self.nframes == other.nframes:
            d['nframes'] = (self.nframes, other.nframes)
        if not self.scalingfactor == other.scalingfactor:
            d['scalingfactor'] = (self.scalingfactor, other.scalingfactor)
        if not self.unit == other.unit:
            d['unit'] = (self.unit, other.unit)
        if ('nchannels' not in d) and ('nframes' not in d):
            blocklen = int(self.fs)
            nframesdifferent = 0
            for i,j in zip(self.iterread_frames(blocklen=blocklen),
                           other.iterread_frames(blocklen=blocklen)):
                nframesdifferent += (i!=j).sum()
            if nframesdifferent > 0:
                d['nframesdifferent'] = nframesdifferent
        if d:
            return d
        else:
            return None

    @property
    def _saveparams(self):
        """the parameters that need to be saved when a child class is
        disk-persistent"""

        return {'duration': duration_string(self.duration),
                'encoding': self.encoding,
                'fs': self.fs,
                'metadata': dict(self.metadata),
                'nchannels': self.nchannels,
                'nframes': self.nframes,
                'origintime': self.origintime,
                'scalingfactor': self.scalingfactor,
                'sndtype': self._classid,
                'sndversion': self._version,
                'startdatetime': str(self.startdatetime),
                'unit': self._unit
                }

    def info(self):
        return self._saveparams

    def samplingtimes(self):
        """
        Returns the times of *sample centers*, relative to origin time.

        To get the sampling times relative to starttime add the starttime and
        origintime to the result of this method (e.g. signal.samplingtimes +
        signal.starttime + signal.origintime). But if you do this, note that
        the samplingtimes property is a float array of 64-bit precision. If
        starttime is a large number (e.g. Epoch) you may want to upcast to
        higher-precision floats first (96- or 128-bit float) if possible on
        your platform, at least if you want to retain precision.

        """
        return ((np.arange(self._nframes, dtype=np.float64) + 0.5)
                / self._fs) - self.origintime

    def samplingboundarytimes(self):
        """
        Returns the times of *sample boundaries*, relative to origin time.

        Note that the size of the return array is ntimesamples + 1

        """
        return (np.arange(self._nframes + 1, dtype=np.float64) / self._fs) \
               - self.origintime

    def time_to_index(self, time, nearest_boundary=False):
        """
        Converts a time, or array of times, to their corresponding sample
        indices.

        Note that the default is to return to which *sample center* the given
        time is closest. When nearest_boundary is True, this will be to which
        *sample start* the time is closest.

        Parameter
        ---------

        time: <float, float sequence>

        nearest_boundary: bool
            Determines whether or not the the sample index is given of which
            the *center* is closest to the parameter time. If True, this will
            be the closest sample *start*.

        Example: if the time parameter is [t0, t1, t2],

        |    s0    |    s1    |    s2    |    s3    |    s4    | ...
                     ^       ^  ^
                     t0      t1 t2

        then the result will be the sample of indices [s1, s1, s2] if
        nearest_boundary is False (default) or [s1, s2, s2] if nearest_boundary
        is True.

        Note that it is possible to get an index number of ntimesamples
        if the time is endtime.

        """
        time = np.asarray(time, dtype=np.float64)
        outsiderange = (time < 0 | time > self.duration)
        if outsiderange.any():
            offendingtimes = time[outsiderange]
            raise ValueError(
                "%s s. are outside range of possible times (%f,%f)" \
                % (offendingtimes, 0, self.duration))
        # calculate
        if nearest_boundary:
            index = (np.floor((time + self.origintime + self.dt / 2.0)
                              * self._fs)).astype(np.int64)
        else:
            index = (np.floor((time + self.origintime)
                              * self._fs)).astype(np.int64)
        if index.size == 1:
            return index.item()
        else:
            return index

    def index_to_time(self, index):
        """
        Converts a sample index, or array of indices, to their
        corresponding times. Note that the *time of sample center*
        is given, not the time of the sample start.

        Parameter
        ---------
        index: an integer or array of integers

        Note
        ----
        Center of samples define their time of occurrence

        |    0    |    1    |    2    |    3    |    4    | ...
             ^         ^         ^         ^         ^
             t0        t1        t2        t3        t4

        """
        index = np.asarray(index, np.int64)
        if ((index < 0) | (index >= self._nframes)).any():
            raise ValueError("index (%s) cannot be smaller than zero or higher"
                             " than nframes - 1 (%d)" \
                             % (index, self._nframes - 1))
        result = ((index + 0.5) / self._fs) - self.origintime
        if result.size == 1:
            return result.item()
        else:
            return result

    # FIXME what about origintime?
    def _check_episode(self, *args, startframe=None, endframe=None,
                       starttime=None, endtime=None, startdatetime=None,
                       enddatetime=None, **kwargs):

        return check_episode(startframe=startframe, endframe=endframe,
                             starttime=starttime, endtime=endtime,
                             startdatetime=startdatetime,
                             enddatetime=enddatetime,
                             fs=self._fs, nframes=self._nframes,
                             originstartdatetime=self.startdatetime)

    def frameindex_to_sndtime(self, frameindex, where='start'):
        frameindex = np.asanyarray(frameindex)
        if where == 'start':
            return frameindex * self.dt
        elif where == 'center':
            return (0.5 + frameindex) * self.dt
        elif where == 'end':
            return (1 + frameindex) * self.dt
        else:
            raise ValueError(f"'where' argument should be either 'start', "
                             f"'center', or 'end', not '{where}'")

    def frameindex_to_epochtime(self, frameindex, where='start'):
        epochtime = self.startepochtime
        if epochtime is not None:
            return self.frameindex_to_sndtime(frameindex, where=where) + \
                   epochtime
        else:
            return None

    def frameindex_to_datetime(self, frameindex, where='start'):
        sndtime = self.frameindex_to_sndtime(frameindex=frameindex,
                                             where=where)
        if str(self.startdatetime) == "NaT":
            return np.datetime64('NaT')
        else:
            return self.startdatetime + \
                   np.round(sndtime * 1e9).astype('timedelta64[ns]')

    # fixme origin time?
    def sndtime_to_datetime(self, time):
        if str(self.startdatetime) == "NaT":
            return None
        else:
            time = np.round(np.asanyarray(time) * 1e9).astype(
                'timedelta64[ns]')
            return self.startdatetime + time

    # this method should be implemented by child class if frames is not
    # numpy-like
    @wraptimeparamsmethod
    def read_frames(self, startframe=None, endframe=None, starttime=None,
                    endtime=None, startdatetime=None, enddatetime=None,
                    channelindex=None, dtype='float64',
                    normalizeaudio=False):
        pass

    @contextmanager
    def open(self):
        yield None

    @wraptimeparamsmethod
    def iterread_frames(self, blocklen=44100, stepsize=None,
                        include_remainder=True, startframe=None, endframe=None,
                        starttime=None, endtime=None, startdatetime=None,
                        enddatetime=None, channelindex=None,
                        firstblocklen=None,
                        dtype=None, normalizeaudio=False):
        with self.open():
            if firstblocklen is not None:
                if firstblocklen > endframe:
                    raise ValueError(f'`firstblocklen` {firstblocklen} is larger '
                                     f'than `endframe` ({endframe})')
                else:
                    yield self.read_frames(startframe=startframe,
                                      endframe=firstblocklen,
                                      channelindex=channelindex, dtype=dtype)
                    startframe += firstblocklen
            for windowstart, windowend in iter_timewindowindices(
                    ntimeframes=self._nframes,
                    framesize=blocklen,
                    stepsize=stepsize,
                    include_remainder=include_remainder,
                    startindex=startframe,
                    endindex=endframe):
                yield self.read_frames(startframe=windowstart,
                                       endframe=windowend,
                                       channelindex=channelindex,
                                       dtype=dtype,
                                       normalizeaudio=normalizeaudio)

    @wraptimeparamsmethod
    def read(self, startframe=None, endframe=None, starttime=None,
             endtime=None, startdatetime=None, enddatetime=None,
             channelindex=None, dtype=None, normalizeaudio=False):
        frames = self.read_frames(startframe=startframe, endframe=endframe,
                                  channelindex=channelindex, dtype=dtype,
                                  normalizeaudio=normalizeaudio)
        startdatetime = self.frameindex_to_datetime(startframe,
                                                    where='start')
        origintime = self.origintime - startframe / float(self.fs)
        if self.metadata is not None:
            metadata = dict(self.metadata)
        else:
            metadata = None
        s = Snd(frames=frames, fs=self._fs,
                startdatetime=startdatetime,
                origintime=origintime,
                metadata=metadata,
                encoding=self.encoding)
        s.starttime = startframe / float(self._fs)
        return s

    @wraptimeparamsmethod
    def iterread(self, startframe=None, endframe=None, starttime=None, endtime=None,
                 startdatetime=None, enddatetime=None, blocklen=None,
                 stepsize=None, include_remainder=True, channelindex=None,
                 splitonclockhour=False, copy=False, dtype=None,
                 normalizeaudio=False):
        if splitonclockhour:
            hour = int(round(self.fs * 60 * 60))
            if blocklen is None:
                blocklen = hour
            if not blocklen == hour:
                raise ValueError(f'`splitonclockhour` parameter not '
                                 f'compatible with `blocklen` {blocklen} that'
                                 f'does not correspond to one hour')
            if self.startdatetime == np.datetime64('NaT'):
                raise ValueError(f'`splitonclockhour` parameter not possible '
                                 f'when there is no known sound startdatetime')
            firstblocklen = int(round(calcsecstonexthour(self.startdatetime) * self.fs))
        else:
            firstblocklen = None
        nread = 0
        if blocklen is None:
            blocklen = int(round(self.fs))
        for window in self.iterread_frames(blocklen=blocklen,
                                           stepsize=stepsize,
                                           include_remainder=include_remainder,
                                           startframe=startframe,
                                           endframe=endframe,
                                           channelindex=channelindex,
                                           firstblocklen=firstblocklen,
                                           dtype=dtype,
                                           normalizeaudio=normalizeaudio):
            if copy:
                window = window.copy()
            elapsedsec = (nread + startframe) * self.dt
            if str(self.startdatetime) == 'NaT':
                startdatetime = 'NaT'
            else:
                startdatetime = self.startdatetime + \
                                np.timedelta64(int(elapsedsec * 1e9), 'ns')
            origintime = self.origintime - elapsedsec
            yield Snd(frames=window, fs=self._fs, startdatetime=startdatetime,
                      origintime=origintime, metadata=None, encoding=self.encoding)
            nread += window.shape[0]

    # FIXME normalization etc
    def to_audiofile(self, path, format=None, encoding=None, endian=None,
                     startframe=None, endframe=None, starttime=None, endtime=None,
                     startdatetime=None, enddatetime=None, channelindex=None,
                     accessmode='r', overwrite=False):
        """
        Save sound object to an audio file.

        Parameters
        ----------
        path
        format
        encoding
        endian
        startframe: {int, None}
            The index of the frame at which the exported sound should start.
            Defaults to None, which means the start of the sound (index 0).
        endframe: {int, None}
            The index of the frame at which the exported sound should end.
            Defaults to None, which means the end of the sound.
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
        import soundfile as sf
        from .audiofile import AudioFile, defaultaudioformat, \
            defaultaudioencoding, availableaudioencodings, availableaudioformats
        startframe, endframe = self._check_episode(startframe=startframe,
                                                   endframe=endframe,
                                                   starttime=starttime,
                                                   endtime=endtime,
                                                   startdatetime=startdatetime,
                                                   enddatetime=enddatetime)
        if encoding is None:
            try:
                encoding = self.encoding
            except:
                encoding = dtypetoencoding(self.framedtype)
        if format is None:
            try:
                format = self.fileformat
            except:
                format = defaultaudioformat
        format = format.upper()
        sf._format_int(format, encoding, endian)
        if format not in availableaudioformats:
            raise ValueError(f"'{format}' format not availabe (choose from: "
                             f"{availableaudioformats.keys()})")
        if encoding is None:
            if isinstance(self, AudioFile):
                if self._audioencoding in availableaudioencodings(format):
                    encoding = self._audioencoding
            else:
                encoding = defaultaudioencoding[format]
        path = Path(path)
        if path.suffix != f'.{format.lower()}':
            path = path.with_suffix(f'.{format.lower()}')
        samplerate = int(round(self.fs))
        if path.exists() and not overwrite:
            raise IOError(
                "File '{}' already exists; use 'overwrite'".format(path))
        if channelindex is not None:
            nchannels = len(np.ones([1, self.nchannels])[0, channelindex])
        else:
            nchannels = self.nchannels
        startdatetime = self.frameindex_to_datetime(startframe,
                                                    where='start')
        origintime = self.origintime - startframe / float(self.fs)
        with sf.SoundFile(file=str(path), mode='w', samplerate=samplerate,
                          channels=nchannels, subtype=encoding, endian=endian,
                          format=format) as f:
            for window in self.iterread_frames(blocklen=samplerate,
                                            startframe=startframe,
                                            endframe=endframe,
                                            channelindex=channelindex):
                f.write(window)
            endian = f.endian
        info = self._saveparams
        info.update({'endiannes': endian,
                     'fileformat': format,
                     'encoding': encoding,
                     'metadata': self.metadata,
                     'sndtype': AudioFile._classid,
                     'startdatetime': startdatetime,
                     'origintime': origintime})
        sndinfopath = Path(f'{path}{SndInfo._suffix}')
        _create_sndinfo(sndinfopath, d=info, overwrite=overwrite)
        return AudioFile(path, accessmode=accessmode)

    #FIXME wrap
    #@wraptimeparamsmethod
    def to_darrsnd(self, path=None, dtype=None, metadata=None, mode='r',
                   startframe=None, endframe=None, starttime=None, endtime=None,
                   startdatetime=None, enddatetime=None, blocklen=44100,
                   accessmode='r', overwrite=False, channelindex=None):

        from .darrsnd import DarrSnd

        snds = self.iterread(startframe=startframe, endframe=endframe,
                               channelindex=channelindex,
                               blocklen=blocklen)
        snd1, snds = peek_iterable(snds)
        sndpath = Path(path)
        if sndpath.suffix not in (SndInfo._suffix, SndInfo._suffix.upper()):
            sndpath = path.with_suffix(SndInfo._suffix)
        darrpath = sndpath.with_suffix('.darr')
        frames = (snd.read_frames() for snd in snds)
        asarray(path=darrpath, array=frames, dtype=dtype,
                accessmode=accessmode, overwrite=overwrite)
        d = self._saveparams  # standard params that need saving
        _create_sndinfo(sndpath, d=d, overwrite=overwrite)
        return DarrSnd(sndpath, accessmode=accessmode)



    def to_audiosnd(self, path, format=None, encoding=None, endian=None,
                    startframe=None, endframe=None, starttime=None,
                    endtime=None, startdatetime=None, enddatetime=None,
                    channelindex=None, accessmode='r', overwrite=False):

        from .audiofile import AudioSnd
        af = self.to_audiofile(path, format=format, encoding=encoding,
                               endian=endian, startframe=startframe,
                               endframe=endframe, starttime=starttime,
                               endtime=endtime, startdatetime=startdatetime,
                               enddatetime=enddatetime, overwrite=overwrite,
                               channelindex=channelindex)
        path = af.audiofilepath.with_suffix(SndInfo._suffix)
        return af.as_audiosnd(accessmode=accessmode, overwrite=overwrite)

    # also share code with darr case
    @wraptimeparamsmethod
    def to_chunkedaudiofile(self, path, chunklen=None, format=None, subtype=None, endian=None,
                            startframe=None, endframe=None, starttime=None, endtime=None,
                            startdatetime=None, enddatetime=None, channelindex=None,
                            splitonclockhour=False, overwrite=False):

        from .chunkedsnd import ChunkedSnd

        if chunklen is None:
            chunklen = int(round(self.fs * 60 * 60))
        dd = create_datadir(path=path, overwrite=overwrite)
        fnames = []
        nframes = 0
        for i, s in enumerate(self.iterread(blocklen=chunklen,
                                            startframe=startframe,
                                            endframe=endframe,
                                            splitonclockhour=splitonclockhour,
                                            channelindex=channelindex)):
            if s.startdatetime != 'NaT':
                ts = str(s.startdatetime)
                secs, ns = ts.rsplit('.')
                if int(ns) == 0: # no part of second
                    ts = secs
                ts = ts.replace(':', '_').replace('.', '_')
            else:
                ts = duration_string(nframes / self.fs)
            fname = f'chunk_{i:0>3}_{ts}'
            af = s.to_audiofile(dd.audiofilepath / fname, format=format,
                                encoding=subtype, endian=endian,
                                overwrite=overwrite)
            fnames.append(af.audiofilepath.name)
            if i == 0:
                s0 = s
            nframes += s.nframes
        d = self._saveparams
        d.update = {'chunktype': 'AudioFile',
                    'chunkpaths': fnames,
                    'fileformat': af.fileformat,
                    'fileformatsubtype': af.fileformatsubtype,
                    'endianness': af.endianness,
                    'nchannels': s0.nchannels,
                    'origintime': s0.origintime,
                    'startdatetime': str(s0.startdatetime)}
        dd.write_sndinfo(d=d, overwrite=overwrite)
        if (self.metadata is not None) and (not overwrite):
            dd.metadata.update(self.metadata)
        return ChunkedSnd(path)

    @wraptimeparamsmethod
    def to_chunkeddarrsnd(self, path, chunklen=None, startframe=None,
                          endframe=None, starttime=None, endtime=None,
                          startdatetime=None, enddatetime=None,
                          channelindex=None, dtype=None, overwrite=False):

        from .chunkedsnd import ChunkedSnd

        if chunklen is None:
            chunklen = int(round(self.fs * 60 * 60))
        dd = create_datadir(path=path, overwrite=overwrite)
        fnames = []
        nframes = 0
        for i, s in enumerate(
                self.iterread(blocklen=chunklen, startframe=startframe,
                              endframe=endframe, channelindex=channelindex)):
            if s.startdatetime != 'NaT':
                ts = str(s.startdatetime)
                secs, ns = ts.rsplit('.')
                if int(ns) == 0: # no part of second
                    ts = secs
                ts = ts.replace(':', '_').replace('.', '_')
            else:
                ts = duration_string(nframes / self.fs)
            fname = f'chunk_{i:0>3}_{ts}'
            af = s.to_darrsnd(dd.audiofilepath / fname, dtype=dtype,
                              metadata=None,
                              overwrite=overwrite)
            fnames.append(af.audiofilepath.name)
            if i == 0:
                s0 = s
            nframes += s.nframes
        d = self._saveparams
        d.update = {'chunktype': 'DarrSnd',
                    'chunkpaths': fnames,
                    'dtype': s0.dtype,
                    'nchannels': s0.nchannels,
                    'origintime': s0.origintime,
                    'startdatetime': str(s0.startdatetime)}
        dd.write_sndinfo(d=d, overwrite=overwrite)
        if (self.metadata is not None) and (not overwrite):
            dd.metadata.update(self.metadata)
        return ChunkedSnd(path)

def dtypetoencoding(dtype):
    mapping = {'uint8': 'PCM_U8',
               'int8': 'PCM_S8',
               'int16': 'PCM_16',
               'int32': 'PCM_32',
               'float32': 'FLOAT',
               'float64': 'DOUBLE'}
    dtype = np.dtype(dtype)
    if not dtype.name in mapping:
        raise TypeError(f"dtype '{dtype.name}' is not supported")
    return mapping[dtype.name]


# FIXME rename this to RAMSnd?
class Snd(BaseSnd):

    _classid = 'Snd'
    _classdescr = 'a sound in RAM memory'

    """A sound in RAM memory.
    
    Parameters
    ----------
    frames: array-like
        Pressure values with time on first axis and channel on second axis. Frames are 
        always two-dimensional. If the input is one-dimensional it is assumed to have 
        one channel only and will be converted to a two-dimensional array with length 1 
        on the second axis.
    fs: int or float
        Sampling rate in Hz (frames per second).
    dtype: numpy dtype {None | unint8 | int8 | int16 | int32 | int64 | float32 | float64 }
        Frames will be converted to this dtype if not None. Default: None, inferred from 
        `frames`.
    encoding: str
        The audio encoding (if known) of the frames. This is different from `framedtype`,  
        which determines how the frame array is numerically represented in RAM memory. 
        The encoding, in contrast, provides information on the representation had before 
        they were converted to this. This may be relevant when reading and saving audio 
        files. For example, the data may originate from a file in PCM_24 format, which has 
        24-bit integer encoding. This will be converted to an int32 numpy array because 
        24-bit numpy arrays do not exist. When saving (parts of) the data into an audio 
        file again, this can be safely done in PCM_24 instead of PCM_32 if it is known 
        that that was the original format. If it is not known, a suitable encoding will be 
        inferred from the dtype of the frames array: 
        
            uint8:  PCM_U8
            int8:    PCM_S8
            int16:   PCM_16
            int32:   PCM_32
            float32: FLOAT
            float64: DOUBLE
    
    """

    def __init__(self, frames, fs, startdatetime='NaT',
                 origintime=0.0, metadata=None, dtype=None,
                 scalingfactor=None, encoding=None, unit=None):
        frames = np.asarray(frames, dtype=dtype)
        if encoding is None:
            encoding = dtypetoencoding(frames.dtype)
        if frames.ndim == 1:
            frames = frames.reshape(-1, 1)
        elif frames.ndim > 2:
            raise ValueError(f"`frames` has to have 2 dimensions (now: {frames.ndim})")
        nframes, nchannels = frames.shape
        self._frames = frames
        if dtype is None:
            dtype = frames.dtype.name
        BaseSnd.__init__(self, nframes=nframes, nchannels=nchannels, fs=fs,
                         framedtype=dtype, scalingfactor=scalingfactor,
                         startdatetime=startdatetime, origintime=origintime,
                         encoding=encoding, metadata=metadata, unit=unit)

    def __str__(self):
        return f'{super().__str__()[:-1]}, {self.framedtype}>'

    __repr__ = __str__

    @wraptimeparamsmethod
    def read_frames(self, startframe=None, endframe=None, starttime=None,
                    endtime=None, startdatetime=None, enddatetime=None,
                    channelindex=None, dtype=None, order='K', ndmin=2,
                    normalizeaudio=False):
        if channelindex is None:
            channelindex = slice(None,None,None)
        frames = self._frames[slice(startframe, endframe), channelindex]
        frames = np.array(frames, copy=True, dtype=dtype, order=order,
                          ndmin=ndmin)
        if normalizeaudio:  # 'int32', 'int16'
            if frames.dtype == np.int32:
                frames *= 1 / 0x80000000
            elif frames.dtype == np.int16:
                frames *= 1 / 0x8000
            else:
                raise TypeError(f"'normalizeaudio' parameter is "
                                f"True, but can only applied to int16 and "
                                f"int32 data; received {frames.dtype} "
                                f"data.")
        if self.scalingfactor is not None:
            frames *= self.scalingfactor

        return frames




