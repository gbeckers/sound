import unittest
import numpy as np
from sound import Snd


class TestSnd(unittest.TestCase):

    def test_numpyframes(self):
        frames = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
                          dtype='float64').reshape(-1,1)
        snd = Snd(frames=frames, samplingrate=10)
        self.assertTrue((snd.read_frames() == frames).all())

    def test_numpyframes1d(self):
        frames = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], dtype='float64')
        snd = Snd(frames=frames, samplingrate=10)
        self.assertTrue((snd.read_frames() == frames.reshape(-1,1)).all())

    def test_nchannels(self):
        frames = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], dtype='float64')
        snd = Snd(frames=frames, samplingrate=10)
        self.assertEqual(snd.nchannels, 1)
        frames = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
                          dtype='float64').reshape(-1, 1)
        snd = Snd(frames=frames, samplingrate=10)
        self.assertEqual(snd.nchannels, 1)
        frames = np.array([[0, 1], [2, 3], [4, 5], [6, 7], [8, 9]],
                           dtype='float64')
        snd = Snd(frames=frames, samplingrate=10)
        self.assertEqual(snd.nchannels, 2)
        frames = np.array([[0, 1, 2, 3], [4, 5, 6, 7]],
                          dtype='float64')
        snd = Snd(frames=frames, samplingrate=10)
        self.assertEqual(snd.nchannels, 4)

    def test_nframes(self):
        frames = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], dtype='float64')
        snd = Snd(frames=frames, samplingrate=10)
        self.assertEqual(snd.nframes, 10)
        frames = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
                          dtype='float64').reshape(-1, 1)
        snd = Snd(frames=frames, samplingrate=10)
        self.assertEqual(snd.nframes, 10)
        frames = np.array([[0, 1], [2, 3], [4, 5], [6, 7], [8, 9]],
                           dtype='float64')
        snd = Snd(frames=frames, samplingrate=10)
        self.assertEqual(snd.nframes, 5)
        frames = np.array([[0, 1, 2, 3], [4, 5, 6, 7]],
                          dtype='float64')
        snd = Snd(frames=frames, samplingrate=10)
        self.assertEqual(snd.nframes, 2)







