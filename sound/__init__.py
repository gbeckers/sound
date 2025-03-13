from .snd import Snd
from .segmented import SegmentedSndFiles
from .sndcollection import SndDict, as_snddict
from .sndfile import *
from .audioimport import *

from .stats import *


from .tests import test
from . import _version
__version__ = _version.get_versions()['version']
