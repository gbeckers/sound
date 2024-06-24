import os
import numpy as np
from pathlib import Path
from .audiofile import AudioFile, defaultaudioencoding
from .darrsnd import DarrSnd

import fnmatch
import os
import re


def findfiles(which, where='.'):
    '''Returns list of filenames from `where` path matched by 'which'
       shell pattern. Matching is case-insensitive.'''

    # TODO: recursive param with walk() filtering
    rule = re.compile(fnmatch.translate(which), re.IGNORECASE)
    return [name for name in os.listdir(where) if rule.match(name)]


validextensions = {f'.{k}' for k in defaultaudioencoding.keys()} # audio file extensions
validextensions |= {ve.lower() for ve in validextensions} # lowercase
validextensions |= ({'.darrsnd', '.DARRSND'})
validextensions |= ({'.audiosnd', '.AUDIOSND'})


def list_audiofiles(audiodir, extensions=None,
                    filenames=None, recursive=True):
    if recursive == True:
        globpattern = '**/*'
    else:
        globpattern = '*'
    if extensions is None:
        extensions = validextensions
    if not filenames is None:
        paths = [Path(audiodir / f) for f in filenames
                  if (Path(audiodir) / f).isfile()
                      and ((Path(audiodir) / f).suffix in extensions)]
    else:
        paths = []
        for path in Path(audiodir).glob(globpattern):
            if path.suffix in extensions:
                paths.append(path)
        paths = [p for p in paths if p.parent not in paths] # to remove audiofiles in audiosnd objects
        paths = sorted(paths)
    if len(paths) == 0:
        raise IOError(
            "there are no ({}) files in {}".format(extensions, audiodir))
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
        sndinfo['fs'].append(snd.fs)
        sndinfo['nframes'].append(snd.nframes)
        sndinfo['audiofileformat'].append(snd.fileformat)
        sndinfo['audioencoding'].append(snd.fileformatsubtype)
        sndinfo['endianness'].append(snd.endianness)
    return sndinfo

# if assertsametype:
#     for key in ('fs','nchannels','format', 'subtype', 'endianness'):
#         ar = np.array(sndinfo[key])
#         if not (ar == ar[0]).all():
#             raise ValueError(
#                 f'not all audio files have the same {key} ({ar})')


