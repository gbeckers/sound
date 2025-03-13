import numpy as np
from pathlib import Path
from .sndfile import SndFile
from .audiofile import AudioFile
from .utils import commonstartsubstring, duration_string, write_jsonfile

import fnmatch
import os
import re

__all__ = ['segmentedaudiofiles_to_snd', 'audiochannelfiles_to_snd',
           'segmentedaudiochannelfiles_to_snd']


def findfiles(which, where='.'):
    '''Returns list of filenames from `where` path matched by 'which'
       shell pattern. Matching is case-insensitive.'''

    # TODO: recursive param with walk() filtering
    rule = re.compile(fnmatch.translate(which), re.IGNORECASE)
    return [name for name in os.listdir(where) if rule.match(name)]


def list_audiofiles(filepaths):
    paths = [Path(f) for f in filepaths]
    sndinfo = {
        'paths': [],
        'nchannels': [],
        'fs': [],
        'nframes': [],
        'audiofileformat': [],
        'audioencoding': [],
        'endianness': [],
    }
    for path in paths:
        (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(
            path)
        snd = AudioFile(path)
        sndinfo['paths'].append(path)
        sndinfo['nchannels'].append(snd.nchannels)
        sndinfo['fs'].append(snd.samplingrate)
        sndinfo['nframes'].append(snd.nframes)
        sndinfo['audiofileformat'].append(snd.fileformat)
        sndinfo['audioencoding'].append(snd.encoding)
    return sndinfo


def list_audiodir(audiodir, extensions=None, recursive=True):
    if recursive == True:
        globpattern = '**/*'
    else:
        globpattern = '*'
    if extensions is None:
        extensions = ('.wav', '.WAV')
    paths = []
    for path in Path(audiodir).glob(globpattern):
        if path.suffix in extensions:
            paths.append(path)
    paths = sorted([p for p in paths if
                    p.parent not in paths])
    return list_audiofiles(paths)

# def audiodir_to_snd(path, extensions=None, origintime=0.0,
#                     startdatetime='NaT', metadata=None, dtype=None,
#                     overwrite=False):
#     sndinfo = list_audiodir(path, extensions=extensions, recursive=False)
#     paths = [Path(path) for path in sndinfo['paths']]
#     return segmentedaudiofiles_to_snd(paths, origintime=origintime,
#                                     startdatetime=startdatetime,
#                                     metadata=metadata, dtype=dtype,
#                                     overwrite=overwrite)

def audiochannelfiles_to_snd(paths, origintime=0.0, startdatetime='NaT',
                             metadata=None, dtype=None, mmap=False,
                             overwrite=False):
    from .snd import BaseSnd
    from .sndfile import SndChannelFiles
    from darr import DataDir

    if not len(paths) > 1:
        raise ValueError("SndChannelFiles can only be used with multiple "
                         "audio files")
    sndinfo = list_audiofiles(paths)
    snds = [SndFile(path) for path in sndinfo['paths']]
    s0 = snds[0]
    for s in snds[1:]:
        if s.audiofilepath.parent != s0.audiofilepath.parent:
            raise ValueError("channel files must be in same directory")
        if s.nframes != s0.nframes:
            raise ValueError("channel files must be equally long")
        if s.samplingrate != s0.samplingrate:
            raise ValueError("channel files must have same sampling rate")
        if str(s.startdatetime) != str(s0.startdatetime):
            raise ValueError(f"Channel files must have same start datetime"
                             f" ({s.startdatetime} vs "
                             f"{s0.startdatetime})")
        if s._origintime != s0._origintime:
            raise ValueError(f"Channel files must have same origin time"
                             f" ({s._origintime} vs "
                             f"{s0._origintime})")
    if dtype is None:
        dtype = SndChannelFiles._defaultsampledtype
    dtype = BaseSnd._check_dtype(BaseSnd, dtype)
    startdatetime = np.datetime64(startdatetime)
    d = {'sndtype': SndChannelFiles._classid,
         'channelfilepaths': [p.name for p in sndinfo['paths']],
         'fs': sndinfo['fs'][0],
         'audiofileformat': sndinfo['audiofileformat'],
         'audioencoding': sndinfo['audioencoding'],
         'endiannes': sndinfo['endianness'],
         'sampledtype': dtype,
         'nframes': s0.nframes,
         'nchannels': len(sndinfo['paths']),
         'origintime': origintime,
         'startdatetime': str(startdatetime)}
    bd = DataDir(s0.audiofilepath.parent)
    sndinfofilename = commonstartsubstring(d['channelfilepaths'])
    sndinfopath = Path(sndinfofilename + '.sound')
    bd._write_jsondict(sndinfopath, d=d,
                       overwrite=overwrite)
    if metadata is not None:
        bd._write_jsondict(SegmentedSndFiles._metadatapath, d=dict(metadata),
                           overwrite=overwrite)
    return SndChannelFiles(bd.path / sndinfopath, accessmode='r', mmap=map)

def segmentedaudiofiles_to_snd(paths, origintime=0.0, startdatetime=None,
                             metadata=None, dtype=None, mmap=False,
                             overwrite=False):
    from .snd import BaseSnd
    from .segmented import SegmentedSndFiles
    from darr import DataDir

    sndinfo = list_audiofiles(paths)
    snds = [SndFile(path) for path in sndinfo['paths']]
    s0 = snds[0]
    segmentnframes = [s0.nframes]
    if startdatetime is None:
        startdatetime = s0.startdatetime
    startdatetimes = [str(startdatetime)]
    nframescum = s0.nframes
    for s in snds[1:]:
        if startdatetime != 'NaT':
            startdatetime = s0.startdatetime + np.round(1e9 * nframescum / s0.samplingrate).astype('timedelta64[ns]')
            startdatetimes.append(str(startdatetime))
        else:
            startdatetimes.append('NaT')
        segmentnframes.append(s.nframes)
        if s.audiofilepath.parent != s0.audiofilepath.parent:
            raise ValueError("audio files must be in same directory")
        if s.samplingrate != s0.samplingrate:
            raise ValueError("audio files must have same sampling rate")
        if s.nchannels != s0.nchannels:
            raise ValueError("audio files must have same number of channels")
        nframescum += s.nframes

    if dtype is None:
        dtype = SegmentedSndFiles._defaultsampledtype
    dtype = BaseSnd._check_dtype(BaseSnd, dtype)

    d = {'sndtype': SegmentedSndFiles._classid,
         'segmenttype': 'SndFile',
         'segmentfilepaths': [p.name for p in sndinfo['paths']],
         'fs': sndinfo['fs'][0],
         'segmentstartdatetimes': startdatetimes,
         'audiofileformat': sndinfo['audiofileformat'][0],
         'audioencoding': sndinfo['audioencoding'][0],
         'endiannes': sndinfo['endianness'][0],
         'sampledtype': dtype,
         'nchannels': sndinfo['nchannels'][0],
         'origintime': origintime,
         'startdatetime': str(s0.startdatetime),
         'enddatetime': str(s0.startdatetime + np.round(1e9 * nframescum / s0.samplingrate).astype('timedelta64[ns]')),
         'segmentnframes': segmentnframes,
         'nframes': nframescum,
         'duration': duration_string(nframescum / s0.samplingrate)}
    bd = DataDir(sndinfo['paths'][0].parent)
    sndinfofilename = commonstartsubstring(d['segmentfilepaths'])
    sndinfopath = Path(sndinfofilename).with_suffix('.sound')
    bd._write_jsondict(sndinfopath, d=d,
                       overwrite=overwrite)
    if metadata is not None:
        bd._write_jsondict(SegmentedSndFiles._metadatapath, d=dict(metadata),
                           overwrite=overwrite)
    return SegmentedSndFiles(bd.path/sndinfopath, mmap=mmap)

def segmentedaudiochannelfiles_to_snd(paths_or_dir, nchannels, origintime=0.0,
                                      startdatetime=None,
                                      metadata=None, dtype=None, mmap=False,
                                      overwrite=False):
    """Interprets a sequence of files as segments of one continuous
    multichannel recording, where channels have been saved as separate mono
    audio files.

    For example, a two-channel recording with 4 time segements would be stored
    like this:

    channel 1:  |  File 1 |  File 3 |  File 5 |  File 7 |
    channel 2:  |  File 2 |  File 4 |  File 6 |  File 8 |


    Parameters
    ----------
    paths_or_dir
    nchannels
    origintime
    startdatetime
    metadata
    dtype
    mmap
    overwrite

    Returns
    -------

    """
    from .snd import BaseSnd
    from .segmented import  SegmentedSndChannelFiles

    if nchannels <= 1:
        raise ValueError(f"SegmentedAudioChannelFiles can only be used with "
                         f"multiple channels, now nchannels is set to "
                         f"{nchannels}")
    startdatetime = np.datetime64(startdatetime)
    try: # first try if we received a sequence of audio file paths
        sndinfo = list_audiofiles(paths_or_dir)
    except:
        try: # if that didn't work, we try if a directory path was provided
            sndinfo = list_audiodir(paths_or_dir)
        except:
            print(f'cannot interpret "{paths_or_dir}" as a sequence of audio '
                  f'files or a directory containing audio files.')
            raise
    nfiles = len(sndinfo['paths'])
    if not nfiles > 1:
        raise ValueError(f"SegmentedSndChannelFiles can only be used with "
                         f"multiple audio files, received {sndinfo['paths']}")
    if not nfiles % nchannels == 0:
        raise ValueError(f"number of audio files ({nfiles}) not compatible with "
                         f"{nchannels} number of channels ({sndinfo['paths']})")
    nsegments = nfiles // nchannels
    sndsegs = []
    # create a list of segment lists of channels
    afs = []
    for segn in range(nsegments):
        segs = []
        for chn in range(nchannels):
            ach = AudioFile(sndinfo['paths'][segn * nchannels + chn])
            segs.append(ach)
            afs.append(ach)
        sndsegs.append(segs)
    # check if all files are in same directory and have same sampling rate
    af0 = afs[0] # first audiofile
    for s in afs[1:]:
        if s.filepath.parent != af0.filepath.parent:
            raise ValueError("channel files must be in same directory")
        if s.samplingrate != af0.samplingrate:
            raise ValueError("channel files must have same sampling rate")
    # loop over segments
    nframestotal = 0
    startdatetimes = []
    # get file nframes to infer total nframes
    for chans in sndsegs:
        ch0 = chans[0]
        if not np.isnat(startdatetime):
            startdatetimes.append(str(startdatetime + np.round(1e9 * nframestotal / ch0.samplingrate).astype('timedelta64[ns]')))
        else:
            startdatetimes.append(startdatetime)
        nframestotal += ch0._nframes
        for chn in chans[1:]:
            if chn.nframes != ch0.nframes:
                raise ValueError(f"Channel files must be equally long."
                                 f"{ch0.filepath} and {chn.filepath} are not "
                                 f"({ch0.nframes} vs {chn.nframes})")
    if dtype is None:
        dtype = SegmentedSndChannelFiles._defaultsampledtype
    dtype = BaseSnd._check_dtype(BaseSnd, dtype)
    startdatetime = np.datetime64(startdatetime)
    d = {'sndtype': SegmentedSndChannelFiles._classid,
         'filepaths': [[ch.filepath.name for ch in seg] for seg in
                       sndsegs],
         'samplingrate': af0.samplingrate,
         'nframes': nframestotal,
         'origintime': origintime,
         'startdatetime': str(startdatetime),
         'segmentstartdatetimes': startdatetimes,}
    parentpath = af0.filepath.parent
    sndinfofilename = commonstartsubstring([chp for chps in d['filepaths'] for chp in chps])
    sndinfopath = parentpath / Path(sndinfofilename + '.sound')
    write_jsonfile(sndinfopath, data=d, sort_keys=True, indent=4,
                   ensure_ascii=True, skipkeys=False, overwrite=overwrite)
    return SegmentedSndChannelFiles(sndinfopath / sndinfopath, accessmode='r')


# if assertsametype:
#     for key in ('fs','nchannels','format', 'subtype', 'endianness'):
#         ar = np.array(sndinfo[key])
#         if not (ar == ar[0]).all():
#             raise ValueError(
#                 f'not all audio files have the same {key} ({ar})')


