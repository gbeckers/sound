import numpy as np
from pathlib import Path
from .snd import Snd
from .audiofile import AudioFile, audiofloat_to_PCM_factor, encodingtodtype


__all__ = ['testaudiofile', 'noise_PCM', 'sine_DOUBLE', 'sine_PCM']




def sine_DOUBLE(f=441., nframes=441, fs=44100):
    t = np.arange(nframes, dtype='float64') / fs
    p = np.sin(2*np.pi*f*t)
    return Snd(p, fs=fs)

# FIXME dtype could be lower in case of 16 or 8 bit PCM
def sine_PCM(f=441., nframes=441, fs=44100, encoding='PCM_32'):
    snd = sine_DOUBLE(f=f, nframes=nframes, fs=fs)
    factor = audiofloat_to_PCM_factor[encoding]
    frames = np.round(snd._frames * factor).astype(encodingtodtype[encoding])
    return Snd(frames, fs=snd.fs, metadata=snd.metadata, encoding=encoding)

def noise_DOUBLE(nframes=441, fs=44100, seed=None):
    if seed is None:
        seed = np.random.randint(1000000)
    np.random.seed(seed)
    p = 2 * (np.random.random(nframes) - 0.5)
    return Snd(p, fs=fs, metadata={'seed': seed})

# FIXME dtype could be lower in case of 16 or 8 bit PCM
def noise_PCM(nframes=441, fs=44100, seed=None, encoding='PCM_32'):
    snd = noise_DOUBLE(nframes=nframes, fs=fs, seed=seed)
    factor = audiofloat_to_PCM_factor[encoding]
    frames = np.round(snd._frames * factor).astype(encodingtodtype[encoding])
    return Snd(frames, fs=snd.fs, metadata=snd.metadata, encoding=encoding)


def testaudiofile():
    p = Path(__file__).parent.absolute() / 'testsndfiles' / 'testsnd_zf_PCM_24.wav'
    return AudioFile(p)

