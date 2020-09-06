from darr.basedatadir import BaseDataDir, create_basedatadir
from darr.metadata import MetaData
from ._version import get_versions

#TODO: required keys for sndinfo

class DataDir(BaseDataDir):

    _classid = 'DataDir'
    _classdescr = 'object for IO for disk-persistent sounds'
    _version = get_versions()['version']
    _suffix = '.snd'
    _sndinfopath = 'sndinfo.json' # here goes required sound information
    _metadatapath = 'metadata.json' # here goes extra information

    def __init__(self, path, accessmode='r'):
        BaseDataDir.__init__(self, path)
        self._metadata = MetaData(self.path / self._metadatapath,
                                  accessmode=accessmode)

    @property
    def metadata(self):
        """Dictionary-like access to disk based metadata.

        Metadata items can be anything that can be saved in JSON format. If
        there is no metadata, the metadata file does not exist, rather than
        being empty. This saves a block of disk space (potentially 4kb)."""

        return self._metadata

    def read_sndinfo(self):
        return self._read_jsondict(self._sndinfopath)

    def write_sndinfo(self, d, overwrite=False):
        self._write_jsondict(self._sndinfopath, d=d,
                                     overwrite=overwrite)
        self.read_sndinfo()


def create_datadir(path, overwrite=False):
    dd = create_basedatadir(path=path,overwrite=overwrite)
    return DataDir(dd.path)








