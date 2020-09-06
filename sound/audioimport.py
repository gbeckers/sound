import os
import numpy as np
from soundfile import SoundFile

def list_audiofiles(audiodir, extensions=('.wav', '.WAV'), filenames=None, assertsametype=False):
    if not filenames is None:
        # FIXME there could be some checks here
        paths = filenames
    else:
        audiofiles = [f for f in os.listdir(audiodir)
                      if (os.path.isfile(os.path.join(audiodir, f))
                          and os.path.splitext(f)[1] in extensions)]
        paths = sorted(audiofiles)
    fullpaths = [os.path.join(audiodir, f) for f in paths]
    if len(fullpaths) == 0:
        raise IOError(
            "there are no ({}) files in {}".format(extensions, audiodir))
    nchannelss = []
    fss = []
    sizes = []
    formats = []
    subtypes = []
    endians = []
    for path in fullpaths:
        (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(
            path)
        with SoundFile(path, 'r') as f:
            nchannelss.append(f.channels)
            fss.append(f.samplerate)
            sizes.append(size)
            formats.append(f.format)
            subtypes.append(f.subtype)
            endians.append(f.endian)

    if assertsametype:
        for (attrname, attrs) in (('fs', fss), ('nchannels', nchannelss),('format', formats),
                               ('subtype', subtypes), ('endian', endians)):
            if not (np.array(attrs) == attrs[0]).all():
                raise ValueError(
                    f'not all audio files have the same {attrname} ({attrs})')
    return fullpaths, paths, fss, nchannelss, sizes, formats, subtypes, endians

# FIXME non-numpy way
def _allfilessamenchannels(nchannelss):
    nchannels = nchannelss[0]
    if not (np.array(nchannelss) == nchannels).all():
        raise ValueError(
            'not all audio files have the same number of channels')
    return nchannels

# FIXME non-numpy way
def _allfilessamefs(fss):
    fs = fss[0]
    if not (np.array(fss) == fs).all():
        raise ValueError('not all audio files have the same sampling rate')
    return fs


# # fixme
# def audiodir_to_disksnd(importdir, sndpath,
#                         extensions=('.wav', '.WAV'),
#                         dtype='float32', scalingfactor=None,
#                         startdatetime='NaT', metadata=None, framesize=44100,
#                         overwrite=False):
#     # fixme not necessary
#     fullpaths, filenames, fss, nchannelss, sizes = list_audiofiles(
#         audiodir=importdir,
#         extensions=extensions)
#     nchannels = _allfilessamenchannels(nchannelss)
#     fs = _allfilessamefs(fss)
#     return audiofiles_to_disksnd(audiofilepaths=fullpaths, sndpath=sndpath,
#                                  dtype=dtype, scalingfactor=scalingfactor,
#                                  startdatetime=startdatetime, metadata=metadata,
#                                  framesize=framesize, overwrite=overwrite)

