from darr.utils import write_jsonfile
from darr.metadata import MetaData
from ._version import get_versions

class SndInfo:

    _classid = 'SndInfo'
    _classdescr = 'JSON file with information on sound object'
    _version = get_versions()['version']
    _suffix = '.json'

    def __init__(self, path, settableparams=None, accessmode='r'):
        self._sndinfo = MetaData(path, accessmode=accessmode)
        if settableparams is None:
            settableparams = ()
        self._settableparams = settableparams

    # @property
    # def sndinfo(self):
    #     return self._sndinfo._read()

    def set_writeable(self):
        self._sndinfo.accessmode = 'r+'

    def set_readonly(self):
        self._sndinfo.accessmode = 'r'

    def _check_writeable(self):
        if self._sndinfo.accessmode != 'r+':
            raise IOError(f"{self._classid} is not writeable. Use "
                          "`set_writeable` method to change this")

    def _set_parameter(self, parameter, value, infoparameters):
        self._check_writeable()
        if parameter in self._settableparams:
            infoparameters[parameter] = value
            self._sndinfo.update(infoparameters)
        else:
            raise ValueError(f"cannot set `{parameter}` parameter on this "
                             f"object ({self._classid})")


def _create_sndinfo(path, d, overwrite=False):
    write_jsonfile(path=path, data=d, overwrite=overwrite)





