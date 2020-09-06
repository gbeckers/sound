import json
import numpy as np
from itertools import chain
from functools import wraps

from pathlib import Path

#FIXME remove cruft

integer_types = (int, np.int8, np.int16, np.int32, np.int64,
                      np.uint8, np.uint16, np.uint32, np.uint64)

eps = np.finfo(np.float64).eps

def timeparams(ntimesamples=None, fs=None, duration=None):
    # we need enough info from duration, fs and ntimesamples
    havents = not (ntimesamples is None)
    havefs = not (fs is None)
    havedur = not (duration is None)
    timeparams = np.array([havents, havefs, havedur])
    if not (timeparams.sum() >= 2):
        raise ValueError(
            "at least 2 values are required for duration, ntimesamples, and fs")
    # if havents:
    #     ntimesamples = check_int(ntimesamples, negative=False)
    # if havefs:
    #     fs = check_arg(fs, 'fs')
    # if havedur:
    #     duration = check_arg(duration, 'duration')
    if timeparams.sum() == 2:
        #  now calculate what's missing
        if havents:
            if havefs:
                duration = ntimesamples / fs
            else:  # have duration

                fs = ntimesamples / duration
        else:  # have duration and have fs
            ntimesamples = fs * duration
            if divmod(ntimesamples, 1.0)[1] != 0.0:
                raise ValueError(
                    "duration and fs do not correspond to integer ntimesamples")
            else:
                ntimesamples = int(ntimesamples)
    return (ntimesamples, fs, duration)


def wraptimeparamsmethod(func):
    @wraps(func)
    def func_wrapper(self, startframe=None, endframe=None, starttime=None,
                     endtime=None,
                     startdatetime=None, enddatetime=None,
                     *args, **kwargs):
        startframe, endframe = self._check_episode(startframe=startframe,
                                                endframe=endframe,
                                                starttime=starttime,
                                                endtime=endtime,
                                                startdatetime=startdatetime,
                                                enddatetime=enddatetime)

        return func(self, startframe=startframe, endframe=endframe,
                    *args, **kwargs)
    return func_wrapper

from contextlib import contextmanager
import os.path
import math
import sys
import numpy as np
from numbers import Number
from collections import Set, Mapping, deque

def isgenerator(iterable):
    return hasattr(iterable, '__iter__') and not hasattr(iterable, '__len__')

def check_startendargs(soundstartframe, soundnframes, startframe, endframe):
    soundendframe = soundstartframe + soundnframes
    if startframe is None:
        startindex = soundstartframe
    else:
        startindex = soundstartframe + startframe
    if endframe is None:
        endindex = soundstartframe + soundnframes
    else:
        endindex = soundstartframe + endframe
    if not soundstartframe <= startindex <= soundendframe:
        raise IndexError('startframe out of bounds')
    if not soundstartframe <= endindex <= soundendframe:
        raise IndexError('endframe out of bounds')

    return startindex, endindex

def check_episode(startframe, endframe, starttime, endtime,
                  startdatetime, enddatetime, fs, nframes, originstartdatetime):
    if sum([0 if s is None else 1 for s in (startframe, starttime, startdatetime)]) > 1:
        raise ValueError("At most one start parameter should be provided")
    if sum([0 if s is None else 1 for s in (endframe, endtime, enddatetime)]) > 1:
        raise ValueError("At most one end parameter should be provided")

    if startdatetime is not None:
        starttime = (np.datetime64(startdatetime) - np.datetime64(originstartdatetime)) / \
                    np.timedelta64(1, 's')
    if starttime is not None:
        startframe = int(round(starttime * fs))
    elif startframe is None:
        startframe = 0
    if enddatetime is not None:
        endtime = (np.datetime64(enddatetime) - np.datetime64(originstartdatetime)) / \
                  np.timedelta64(1, 's')
    if endtime is not None:
        endframe = int(round(endtime * fs))
    elif endframe is None:
        endframe = nframes
    if not isinstance(startframe, integer_types):
        raise TypeError(f"'startframe' ({startframe}, {type(startframe)}) "
                        f"should be an int")
    if not isinstance(endframe, integer_types):
        raise TypeError(f"'endframe' ({endframe}, {type(endframe)}) should be "
                        f"an int")
    if not endframe >= startframe:
        raise ValueError(f"'endframe' ({endframe}) lower than 'startframe' "
                         f"({startframe})")
    if endframe > nframes:
        raise ValueError(f"'endframe' ({endframe}) higher than 'nframes' "
                         f"({nframes})")
    if startframe < 0:
        raise ValueError(f"'startframe' ({startframe}) should be >= 0")
    return startframe, endframe


@contextmanager
def tempdir(dir='.', keep=False, report=False):
    import tempfile
    import shutil
    try:
        tempdirname = tempfile.mkdtemp(dir=dir)
        if report:
            print(f'created cache file {tempdirname}')
        yield tempdirname
    except:
        raise
    finally:
        if not keep:
            shutil.rmtree(tempdirname)
            if report:
                print(f'removed cache file {tempdirname}')

# def _check_dir(path):
#     if os.path.isdir(path):
#         return path
#     else:
#         raise ValueError('%s is not a directory' % path)
#
# def _check_fileexists(filename):
#     if not os.path.exists(filename):
#         raise IOError("file '%s' does not exist" % filename)
#     return filename
#
# def _check_notfileexists(filename, overwrite=False):
#     if os.path.exists(filename) and (not overwrite):
#         raise IOError("file '%s' already exist" % filename)
#     return filename
#
# def _check_h5file(path):
#     if not (os.path.exists(path) and (os.path.splitext(path)[-1] == '.h5')):
#         raise IOError("'%s' is not a path to a h5 file" % path)
#     return path
#
# def _check_mode(mode):
#     if mode == 'w':
#         raise IOError("'w' mode is not allowed; delete SoundStore first")
#     if mode not in ('r', 'a', 'r+'):
#         raise IOError("mode can only be 'r', 'a', 'r+'")
#     return mode

def packing_code(samplewidth):
    if samplewidth == 1:            # 8 bits are unsigned, 16 & 32 signed
        return 'B', 128.0        # unsiged 8 bits
    elif samplewidth == 2:
        return 'h', 32768.0        # signed 16 bits
    elif samplewidth == 4:
        return 'i',  32768.0 * 65536.0    # signed 32 bits
    raise ValueError('WaveIO Packing Error: not able to parse {} bytes'.format(samplewidth))


def duration_string(seconds):
    intervals = ((60.*60.*24.*7., 'weeks'),
                 (60.*60.*24., 'days'),
                 (60.*60., 'hours'),
                 (60., 'minutes'),
                 (1., 'seconds'),
                 (0.001, 'milliseconds'))
    for interval in intervals:
        if seconds >= interval[0]:
            amount = seconds/interval[0]
            unit = interval[1]
            if amount < 2.0:
                unit = unit[:-1] # remove 's'
            return f'{amount:.2f} {unit}'
    return f'{seconds/intervals[-1][0]:.3f} {intervals[-1][1][:-1]}'



# def stringcode(number, labels="abcdefghijklmnopqrstuvwxyz", maxnumber=None):
#     nlabels = len(labels)
#     if maxnumber is None:
#         maxnumber = number
#     if maxnumber < number:
#         raise ValueError(f"'maxnumber' should be at least {number}"
#     codelen = int(math.ceil(math.log(maxnumber+1, nlabels)))
#     a,b = divmod(number,nlabels)
#     code = [labels[b]]
#     for i in range(1, codelen):
#         a,b = divmod(a, nlabels)
#         code.insert(0, labels[b])
#     return ''.join(code)


# def getsize(obj):
#     """Recursively iterate to sum size of object & members."""
#     def inner(obj, _seen_ids = set()):
#         obj_id = id(obj)
#         if obj_id in _seen_ids:
#             return 0
#         _seen_ids.add(obj_id)
#         size = sys.getsizeof(obj)
#         if isinstance(obj, zero_depth_bases):
#             pass # bypass remaining control flow and return
#         elif isinstance(obj, (tuple, list, Set, deque)):
#             size += sum(inner(i) for i in obj)
#         elif isinstance(obj, Mapping) or hasattr(obj, iteritems):
#             size += sum(inner(k) + inner(v) for k, v in getattr(obj, iteritems)())
#         # Now assume custom object instances
#         elif hasattr(obj, '__slots__'):
#             size += sum(inner(getattr(obj, s)) for s in obj.__slots__ if hasattr(obj, s))
#         else:
#             attr = getattr(obj, '__dict__', None)
#             if attr is not None:
#                 size += inner(attr)
#         return size
#     return inner(obj)


def fit_frames(totalsize, framesize, stepsize=None):
    """
    Calculates how many frames of 'framesize' fit in 'totalsize',
    given a step size of 'stepsize'.

    Parameters
    ----------
    totalsize: int
        Size of total
    framesize: int
        Size of frame
    stepsize: int
        Step size, defaults to framesize (i.e. no overlap)

    Returns a tuple (nframes, newsize, remainder)
    """

    if ((totalsize % 1) != 0) or (totalsize < 1):
        raise ValueError("invalid totalsize (%d)" % totalsize)
    if ((framesize % 1) != 0) or (framesize < 1):
        raise ValueError("invalid framesize (%d)" % framesize)

    if framesize > totalsize:
        return 0, 0, totalsize

    if stepsize is None:
        stepsize = framesize
    else:
        if ((stepsize % 1) != 0) or (stepsize < 1):
            raise ValueError("invalid stepsize")

    totalsize = int(totalsize)
    framesize = int(framesize)
    stepsize = int(stepsize)

    nframes = ((totalsize - framesize) // stepsize) + 1
    newsize = nframes * stepsize + (framesize - stepsize)
    remainder = totalsize - newsize

    return nframes, newsize, remainder

def iter_timewindowindices(ntimeframes, framesize, stepsize=None,
                                 include_remainder=True, startindex=None,
                                 endindex=None):


    """
    Parameters
    ----------

    framesize: int
        Size of the frame in timesamples. Note that the last frame may be
        smaller than `framesize`, depending on the number of timesamples.
    stepsize: <int, None>
        Size of the shift in time per iteration in number of timesamples.
        Default is None, which means that `stepsize` equals `framesize`.
    include_remainder: <bool, True>
        Determines whether remainder (< framesize) should be included.
    startindex: <int, None>
        Start frame number.
        Default is None, which means to start at the beginning (sample 0)
    endindex: <int, None>
        End frame number.
        Default is None, which means to end at the end.

    Returns
    -------

    An iterator that yield tuples (start, end) representing the start and
    end indices of a time frame of size framesize that moves in stepsize
    steps. If include_remainder is True, it ends with a tuple representing
    the remainder, if present.

    """

    # framesize = check_arg(framesize, 'framesize')
    if stepsize is None:
        stepsize = framesize
    # stepsize = check_arg(stepsize, 'stepsize')
    if startindex is None:
        startindex = 0
    # startindex = check_arg(startindex, 'startindex')
    if endindex is None:
        endindex = ntimeframes
    # endindex = check_arg(endindex, 'startindex')

    if startindex > (ntimeframes - 1):
        raise ValueError("startindex too high")
    if endindex > ntimeframes:
        raise ValueError("endindex is too high")
    if startindex >= endindex:
        raise ValueError(f"startindex ({startindex}) should be lower than endindex ({endindex})")

    nframes, newsize, remainder = fit_frames(
        totalsize=(endindex - startindex),
        framesize=framesize,
        stepsize=stepsize)
    framestart = startindex
    frameend = framestart + framesize
    for i in range(nframes):
        yield framestart, frameend
        framestart += stepsize
        frameend = framestart + framesize
    if include_remainder and (remainder > 0) and (
                framestart < ntimeframes):
        yield framestart, framestart+remainder

# fixme use from diskarray
def write_json(datadict, path, sort_keys=True, indent=4, overwrite=False):
    path = Path(path)
    if (not path.exists()) or overwrite:
        with open(path, 'w') as f:
            f.write(json.dumps(datadict, sort_keys=sort_keys, indent=indent))
    else:
        raise IOError(f"'{path}' exists, use 'overwrite' parameter if "
                      f"appropriate")
# fixme use from diskarray
def read_json(path):
    with open(path, 'r+') as f:
        return json.loads(f.read())


def calcsecstonexthour(datetime):
    datetime = np.datetime64(datetime)
    D, T = str(datetime).split('T')
    h, m, s = T.split(':')
    if (float(m) != 0.0) or (float(s) != 0.0):
        td =  np.datetime64(f'{D}T{int(h) + 1:02d}:00:00') - np.datetime64(f'{D}T{h}:{m}:{s}')
        return td.item().total_seconds()
    else:
        return 0.0

def peek_iterable(iterable):
    gen = (i for i in iterable)
    first = next(gen)
    return first, chain([first], gen)