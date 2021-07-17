from pathlib import Path
from darr.metadata import MetaData
from darr.basedatadir import BaseDataDir, create_basedatadir
from ._version import get_versions

class DiskSnd(BaseDataDir):

    _classid = 'DiskSnd'
    _classdescr = 'disk-persistent sound(s) in a directory with JSON information file'
    _version = get_versions()['version']
    _metadatapath = 'metadata.json'
    _sndinfopath = 'sndinfo.json'
    _suffix = '.snd'

    def __init__(self, path, accessmode='r'):
        BaseDataDir.__init__(path=path)
        self._sndinfo = MetaData(self.path / self._sndinfopath, accessmode='r')
        self._accessmode = accessmode

    @property
    def sndinfo(self):
        return self._sndinfo

    @property
    def accessmode(self):
        return self._accessmode


def _create_disksnd(path, sndinfo, metadata=None, accesmode='r', overwrite=False):
    bdd = create_basedatadir(path, overwrite=overwrite)
    bdd._write_jsondict(DiskSnd._sndinfopath, d=sndinfo)
    if metadata is not None:
        md = MetaData(bdd.path / DiskSnd._metadatapath)
        md.updata(metadata)
    return DiskSnd(path, accesmode=accesmode)

