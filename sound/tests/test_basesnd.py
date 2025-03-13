import unittest
import numpy as np
from sound.snd import BaseSnd

class TestBaseSnd(unittest.TestCase):

    def test_fs_int(self): # int should remain int
        snd = BaseSnd(nframes=2, nchannels=1, samplingrate=10, dtype='float32')
        self.assertEqual(snd.samplingrate, 10)
        self.assertIsInstance(snd.samplingrate, int)

    def test_fs_float(self): #float should remain float
        snd = BaseSnd(nframes=2, nchannels=1, samplingrate=10., dtype='float32')
        self.assertEqual(snd.samplingrate, 10.)
        self.assertIsInstance(snd.samplingrate, float)

    def test_fs_wrongtype(self):
        for fs in (np.float32(10), "10", (10,)):
            self.assertRaises(TypeError, BaseSnd, nframes=2, nchannels=1, fs=fs,
                              dtype='float32')
