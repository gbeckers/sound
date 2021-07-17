import sys
from .darrsnd import DarrSnd, SndInfo
from .audioimport import list_audiofiles
from ._version import get_versions
from .audiofile import AudioSnd, AudioFile
from .darrsnd import DarrSnd
from .chunkedsnd import ChunkedSnd

from pathlib import Path

__all__ = ['SndDict']


# - SndSequence: collection of AudioSnd or DarrSnds
# - _DarrSndArray

##FIXME NOT FINISHED. look at sndstimbuilder
## FIXME why not use a file instead of dir? this enables many dicts on the same dirtree
class SndDict(SndInfo):

    _classid = 'SndDict'
    _classdescr = 'dictionary of disk-based Snds'
    _suffix = '.snddict'
    _fileformat = 'snddict'

    def __init__(self, path, dtype=None, accessmode='r'):
        SndInfo.__init__(self, path=path, accessmode=accessmode)
        ci = self._read_jsondict(self._sndinfopath)
        if not ci['sndtype'] == self._classid:
            raise TypeError(f'{path} is not a SndDict')
        self._sndpaths = []
        self._sndtypes = []
        self._sndkeys = []
        for sndpath,sndtype, key in ci['sndtable']:
            self._sndpaths.append(self.path / sndpath)
            self._sndtypes.append(sndtype)
            self._sndkeys.append(key)

    #enable multiple items
    def __getitem__(self, item):
        i = self._sndkeys.index(item)
        sndclass = getattr(sys.modules[__name__],self._sndtypes[i])
        return sndclass(self._sndpaths[i])

    def __len__(self):
        return len(self._sndkeys)

    def keys(self):
        return tuple(self._sndkeys)




# FIXME when no keys, do not copy filename in json file
# FIXME first does AudioSnd really need a seperate dir.
# FIXME, should metadata not just be a key in AudioSnd extra file?

def as_snddict(path, name, extensions=None, filenames=None, keys=None,
               recursive=True, overwrite=False):
    """Converts a directory of sounds to a SndDict

    If filenames are provided, they should be relative to `path`.

    path: Path or str
        Path to directory with sounds. Subdirectories will be included
        if `recursive` is True.
    name: str
        Name of dictionary. This will be the filename where all object
        info will be saved.

    """
    if filenames is None:
        fileinfo = list_audiofiles(audiodir=path, filenames=filenames,
                                   extensions=extensions,
                                   recursive=recursive)
        filenames = [str(p.relative_to(path)) for p in fileinfo['path']]
    else:
        filenames = [str(Path(fn)) for fn in filenames]
    if keys is None:
        keys = filenames
    sndtable = []
    # FIXME make this a general function
    for fn,key in zip(filenames,keys):
        suffix = Path(fn).suffix
        if suffix in {'.darrsnd', '.DARRSND'}:
            sndtype = 'DarrSnd'
        elif suffix in {'.audiosnd', '.AUDIOSND'}:
            sndtype = 'AudioSnd'
        elif suffix in {'.chunkedsnd', '.CHUNKEDSND'}:
            sndtype = 'ChunkedSnd'
        else:
            sndtype = 'AudioFile'
        sndtable.append([fn, sndtype, key])
    dd = SndInfo(path)
    sndinfo = {
        'sndtype': 'SndDict',
        'soundversion': get_versions()['version'],
        'sndtablecolumns': ['path', 'sndtype', 'name'],
        'sndtable': sndtable
    }
    dd.write_sndinfo(sndinfo,overwrite=overwrite)
    return SndDict(path)