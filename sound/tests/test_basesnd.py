import unittest
import numpy as np
from sound.snd import BaseSnd

class TestBaseSnd(unittest.TestCase):

    def test_fs_int(self): # int should remain int
        snd = BaseSnd(nframes=2,nchannels=1, fs=10, dtype='float32')
        self.assertEqual(snd.fs, 10)
        self.assertIsInstance(snd.fs, int)

    def test_fs_float(self): #float should remain float
        snd = BaseSnd(nframes=2, nchannels=1, fs=10., dtype='float32')
        self.assertEqual(snd.fs, 10.)
        self.assertIsInstance(snd.fs, float)

    def test_fs_wrongtype(self):
        for fs in (np.float32(10), "10", (10,)):
            self.assertRaises(TypeError, BaseSnd, nframes=2, nchannels=1, fs=fs,
                              dtype='float32')
