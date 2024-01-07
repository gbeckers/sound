import numpy as np
from functools import wraps
from .snd import BaseSnd

__all__ = ['max', 'min', 'minmax', 'mean', 'rms']

defaultframesize = 1024 * 1024

# FIXME all stats in one?

def timeparams_decorate(func):
    @wraps(func)
    def func_wrapper(s, startframe=None, endframe=None, starttime=None,
                     endtime=None,
                     startdatetime=None, enddatetime=None,
                     blocklen=defaultframesize, *args, **kwargs):
        #FIXME this should be removed
        if not issubclass(type(s), BaseSnd):
            raise TypeError(
                f"'s' should be a Snd, DiskSnd or AudioFile, not a {type(s)}")
        startframe, endframe = s._check_episode(startframe=startframe,
                                                endframe=endframe,
                                                starttime=starttime,
                                                endtime=endtime,
                                                startdatetime=startdatetime,
                                                enddatetime=enddatetime)
        if blocklen is None or (endframe - startframe) <= blocklen:
            blocklen = endframe
        return func(s, startframe=startframe, endframe=endframe,
                    blocklen=blocklen, *args, **kwargs)

    return func_wrapper

@timeparams_decorate
def rms(s, startframe=None, endframe=None, starttime=None, endtime=None,
        startdatetime=None, enddatetime=None,
        blocklen=defaultframesize, channelindex=slice(None), dtype=None):
    sqsum = 0.
    nframes = 0
    for ar in s.iterread_frames(blocklen=blocklen, startframe=startframe, endframe=endframe, starttime=starttime,
                                endtime=endtime, startdatetime=startdatetime, enddatetime=enddatetime,
                                channelindex=channelindex, include_remainder=True):
        if not np.issubdtype(dtype, ar._framesdtype):
            ar = ar.astype(dtype)
        sqsum += np.sum(ar ** 2.0, axis=s._timeaxis)
        nframes += ar.shape[0]
    return (sqsum / nframes) ** 0.5


@timeparams_decorate
def mean(s, startframe=None, endframe=None, starttime=None, endtime=None,
         startdatetime=None, enddatetime=None,
         blocklen=defaultframesize, channelindex=slice(None), dtype=None):
    tsum = 0.
    nframes = 0
    for ar in s.iterread_frames(blocklen=blocklen, startframe=startframe, endframe=endframe, starttime=starttime,
                                endtime=endtime, startdatetime=startdatetime, enddatetime=enddatetime,
                                channelindex=channelindex, include_remainder=True):
        if not np.issubdtype(dtype, ar._framesdtype):
            ar = ar.astype(dtype)
        tsum += np.sum(ar, axis=s._timeaxis)
        nframes += ar.shape[0]
    return tsum / nframes


@timeparams_decorate
def max(s, startframe=None, endframe=None, starttime=None, endtime=None,
        startdatetime=None, enddatetime=None,
        blocklen=defaultframesize, channelindex=slice(None)):
    omax = np.empty((s._nchannels,), dtype=np.float64)  # overall max
    omax[:] = -np.inf
    for ar in s.iterread_frames(blocklen=blocklen, startframe=startframe, endframe=endframe, starttime=starttime,
                                endtime=endtime, startdatetime=startdatetime, enddatetime=enddatetime,
                                channelindex=channelindex,
                                include_remainder=True):
        omax = np.maximum(np.max(ar, axis=0), omax)
    return omax

@timeparams_decorate
def min(s, startframe=None, endframe=None, starttime=None, endtime=None,
        startdatetime=None, enddatetime=None,
        blocklen=defaultframesize, channelindex=slice(None)):
    omin = np.empty((s._nchannels,), dtype=np.float64)  # overall max
    omin[:] = np.inf
    for ar in s.iterread_frames(blocklen=blocklen, startframe=startframe, endframe=endframe, starttime=starttime,
                                endtime=endtime, startdatetime=startdatetime, enddatetime=enddatetime,
                                channelindex=channelindex,
                                include_remainder=True):
        omin = np.minimum(np.min(ar, axis=0), omin)
    return omin

@timeparams_decorate
def minmax(s, startframe=None, endframe=None, starttime=None, endtime=None,
           startdatetime=None, enddatetime=None,
           blocklen=defaultframesize, channelindex=slice(None)):
    omin = np.empty((s._nchannels,), dtype=np.float64)  # overall max
    omin[:] = np.inf
    omax = np.empty((s._nchannels,), dtype=np.float64)  # overall max
    omax[:] = -np.inf
    for ar in s.iterread_frames(blocklen=blocklen, startframe=startframe, endframe=endframe, starttime=starttime,
                                endtime=endtime, startdatetime=startdatetime, enddatetime=enddatetime,
                                channelindex=channelindex,
                                include_remainder=True):
        omin = np.minimum(np.min(ar, axis=0), omin)
        omax = np.maximum(np.max(ar, axis=0), omax)
    return omin, omax
