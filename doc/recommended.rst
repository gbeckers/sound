Recommended way of working with audio files in science
======================================================
If the source of your sound is an audio file, it is a good idea to keep that
original. I.e. do not delete it after you converted it into something else,
even if that conversion is said to be 'lossless' or if you are saving in a
higher resolution format. Some conversions are theoretically lossless, but
even renowned audio libraries and programs have bugs, so any conversion may
lead to unintended changes. Yes, this really happens in practice.

Further, if you record audio files it is best to use a widely supported
format with sufficient resolution. I recommend 'WAV' and integer 24-bit or
even better 32-bit float LPCM encoding without compression. These are lossless
and widely used formats, reducing the chances that software reading or writing
these files have bugs that potentially change the data.

The WAV format is normally limited to file sizes less than 4 Gb. Recording
equipment will often generate multiple files when the 4 Gb limit is crossed.
In the Sound library, such files of consecutive audio chunks can easily be
accessed as one sound with the ChunkedDiskAudioSnd object.

If you change the data with some transformation it is recommended to
store the results in a 64-bit float format, disk space is not a major
concern. If you do not need an audio file then a float64 `Darr
<https://github.com/gbeckers/Darr>`__ array is a good option
because this maximizes accessibility of your data by other scientific computing
libraries and platforms. Sound will write to Darr arrays. If you need the data
to be coded in an audio format, consider a WAV file in DOUBLE (i.e 64-bit
float) format.

Note on reading and normalizing audio files
===========================================

Under the hood, audio files in Sound are read and written by `SoundFile
<https://github .com/bastibe/SoundFile>`__. The default of SoundFile is to
normalize integer-based formats to float64 in the range of [-1.0,1.0).
This is very convenient for most audio applications, but our intended
use cases include scientific applications in which some of the side effects of
this conversion may be unexpected and unwanted, such as unavoidable (small)
errors when reading and then saving the exact same data in integer encodings
(see `here <http://www.mega-nerd.com/libsndfile/FAQ.html#Q010>`__ why). Also,
rather serious normalization bugs have been reported when reading the common
FLAC format this way (e.g. see
`here <https://github.com/bastibe/SoundFile/issues/265>`__)

Therefore Sound tries to avoid normalization of integer audio data, by
reading it as int16 or int32 instead of float, whenever this is compatible. You
can always normalize explicitly later if you want by converting your sound to a
floating point type. The latter is performed by numpy which is a widely trusted
library for scientific computing.

When reading the widely used PCM_24 format, Sound will convert it to a 32-bit
int representation for in-memory operations, but will automatically use PCM_24
again when saving to an audio file, as long as the data were not transformed in
the meantime.
