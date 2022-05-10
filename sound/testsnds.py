import numpy as np
from pathlib import Path
from .snd import Snd
from .audiofile import AudioFile


__all__ = ['testaudiofile', 'noise_PCM32', 'sine_DOUBLE', 'sine_PCM32']

#  24 bits	−8388608 to 8388607

audiofloat_to_PCM32_factor = 0x7FFFFFFF     # 2147483647
PCM32_to_audiofloat_factor = 1 / 0x80000000 # 1 / 2147483648

def sine_DOUBLE(f=441., nframes=441, fs=44100):
    t = np.arange(nframes, dtype='float64') / fs
    p = np.sin(2*np.pi*f*t)
    return Snd(p, fs=fs)

def sine_PCM32(f=441., nframes=441, fs=44100):
    snd = sine_DOUBLE(f=f, nframes=nframes, fs=fs)
    frames = np.round(snd._frames * audiofloat_to_PCM32_factor).astype('int32')
    return Snd(frames, fs=snd.fs, metadata=snd.metadata)

def noise_DOUBLE(nframes=441, fs=44100, seed=None):
    if seed is None:
        seed = np.random.randint(1000000)
    np.random.seed(seed)
    p = 2 * (np.random.random(nframes) - 0.5)
    return Snd(p, fs=fs, metadata={'seed': seed})

def noise_PCM32(nframes=441, fs=44100, seed=None):
    snd = noise_DOUBLE(nframes=nframes, fs=fs, seed=seed)
    frames = np.round(snd._frames * audiofloat_to_PCM32_factor).astype('int32')
    return Snd(frames, fs=snd.fs, metadata=snd.metadata)


def testaudiofile():
    p = Path(__file__).parent.absolute() / 'testsndfiles' / 'testsnd_zf.wav'
    return AudioFile(p)

