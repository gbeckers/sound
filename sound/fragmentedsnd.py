from .snd import BaseSnd

class FragmentedSnd(BaseSnd):

    def __init__(self, path):
        self._datadir = dd = DataDir(path=path, accessmode=accessmode)
