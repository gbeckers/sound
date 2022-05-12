Important note on integer encodings and normalization
=====================================================

Under the hood, audio files in Sound are read and written by
`SoundFile <https://github.com/bastibe/python-soundfile>`__, which
supports many audio formats and encodings. The default behaviour in
SoundFile is to normalize integer-based formats to float64 in the range of
[-1.0,1.0). This is very convenient for most audio applications, but our
intended use cases include scientific applications in which some of the side
effects of this conversion may be unexpected and unwanted, such as
unavoidable (small) errors when reading and then saving the exact
same data in integer encodings (see
`here <http://www.mega-nerd.com/libsndfile/FAQ.html#Q010>`__ why). Also,
rather serious normalization bugs have been reported when reading the common
FLAC format this way (e.g. see
`here <https://github.com/bastibe/SoundFile/issues/265>`__)

As a consequence, and unlike other libraries, *Sound* does not automatically
normalize values of integer based formats to floats between -1.0 and 1.0
when reading them. (You *can* still read normalized values though when you
specify that you want this.) The reason why *Sound*'s default is to not
normalize is that this process is not lossless if you want to save the data
later, even if it is in the exact same encoding and the data has not
undergone further processing (see
`here <http://www.mega-nerd.com/libsndfile/FAQ.html#Q010>`__ why). The
difference is negligible for audio applications, but being a scientific
library the default in *Sound*  is to avoid potentially lossy normalization
no matter how small. So, if you read a PCM_16 or PCM_32 WAV file, you receive
the integer numbers that as they are stored in the file. If you save them
again without transformation in an audio file *with the same type of encoding
or a higher resolution one*, the result will be lossless. This is useful,
for example, when reading shorter episodes of interest in a long recording and
saving them.

It is good to note though that when reading audio data in a given integer
format (e.g. PCM_16) and then writing the exact same audio data in a higher
resolution integer format (e.g. PCM_24), the latter file will contain
different (larger) numbers and so do the NumPy arrays that you read from them.
This can be surprising at first. The reason for this behavior is that in the
audio world sound amplitude is 'scaled' to the range of possible values in an
encoding. But you do not need to worry about this because these
transformations in *Sound* (which are done by the underlying *SoundFile*
library) are lossless as long as you never convert to an encoding with fewer
bits than your source data.

An example may help to understand this. Say I recorded a sound in PCM_16
encoding in a WAV file, which may contain values between the defined minimum
and maximum of -32768 and 32767, respectively. I will simulate this
recording by generating 10 random values between these limits and create a
Snd object based on them

.. code:: python

    >>> import sound as snd
    >>> import numpy as np
    >>> frames = np.random.randint(low=-32768, high=32767, size=10, dtype='int16')
    >>> s = snd.Snd(frames, fs=44100)
    >>> s.read_frames()
    array([[-25707],
           [ 16978],
           [-10276],
           [ -5900],
           [-26844],
           [ -9111],
           [ -7218],
           [  2237],
           [-28285],
           [   -89]], dtype=int16)

Next I save the sound in a WAV audiofile with PCM_16 encoding.

.. code:: python

    >>> s_saved16 = s.to_audiofile('test_PCM16.wav', encoding='PCM_16')
    >>> s_saved16.read_frames()
    array([[-25707],
           [ 16978],
           [-10276],
           [ -5900],
           [-26844],
           [ -9111],
           [ -7218],
           [  2237],
           [-28285],
           [   -89]], dtype=int16)

Not so surprising. Now, saving the same data but with PCM_32 encoding:

.. code:: python

    >>> s_saved32 = s.to_audiofile('test_PCM32.wav', encoding='PCM_32')
    >>> s_saved32.read_frames()
    array([[-1684733952],
           [ 1112670208],
           [ -673447936],
           [ -386662400],
           [-1759248384],
           [ -597098496],
           [ -473038848],
           [  146604032],
           [-1853685760],
           [   -5832704]], dtype=int32)

Perhaps a bit surprising, but this transformation is lossless because under
the hood the int16 values were simply bit-shifted to the left to fit the
scale of the higher resolution encoding. We can check by bit-shifting to the
right, undoing this:

.. code:: python

    >>> s_saved32 = s.to_audiofile('test_PCM32.wav', encoding='PCM_32')
    >>> np.right_shift(s_saved32.read_frames(), 16)
    array([[-25707],
           [ 16978],
           [-10276],
           [ -5900],
           [-26844],
           [ -9111],
           [ -7218],
           [  2237],
           [-28285],
           [   -89]], dtype=int32)

There is no real reason to 'undo' the scaling in practice, as it has the exact
same information, but it is just done her to show what is going on.

NumPy has no 24-bit int dtypes, so if you read PCM_24 encoding, the results
will be in an int32 array, with automatic scaling to the range of PCM_32.
But as the transformation again is based on a simple bit shift of 8 bits,
there is no loss of information when you save these values again in PCM_24,
in which case the values are shifted back automatically.




