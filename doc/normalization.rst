Important note on reading and normalizing audio files
=====================================================

Under the hood, audio files in Sound are read and written by
`SoundFile <https://github.com/bastibe/python-soundfile>`__. The default of
SoundFile is to normalize integer-based formats to float64 in the range of [-1.0,1.0).
This is very convenient for most audio applications, but our intended
use cases include scientific applications in which some of the side effects of
this conversion may be unexpected and unwanted, such as unavoidable (small)
errors when reading and then saving the exact same data in integer encodings
(see `here <http://www.mega-nerd.com/libsndfile/FAQ.html#Q010>`__ why). Also,
rather serious normalization bugs have been reported when reading the common
FLAC format this way (e.g. see
`here <https://github.com/bastibe/SoundFile/issues/265>`__)

For this reason Sound tries to avoid normalization of integer audio data. It
reads it as int16 or int32 instead of float, whenever this is compatible. You
can always normalize explicitly later if you want by converting your sound to a
floating point type. The latter is performed by numpy which is a widely trusted
library for scientific computing.

When reading the widely used PCM_24 format, Sound will convert it to a 32-bit
int representation for in-memory operations, but will automatically use PCM_24
again when saving to an audio file, as long as the data were not transformed in
the meantime.
