from .snd import BaseSnd

# should be based on a AudioFileChunked
class FragmentedSndFiles(BaseSnd):

    def __init__(self, path):
        self._datadir = dd = DataDir(path=path, accessmode=accessmode)

