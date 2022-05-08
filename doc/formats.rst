# Supported Formats

For reading and writing audio data *Sound* depends on the Python library 
*SoundFile*, which in turn depends on the C library *libsndfile*. In 
addition, *Sound* supports reading and writing in Darr format, which is 
a format for scientific numeric data. The latter is recommended for easy 
readability of data outside of the world of audio (such as tools for 
scientific computing) or when very efficient read access to very large files 
(that do not fit in RAM) is required.

+------------+------+----+-----+-----+------+-----+-------+------+------+-------+------+-----+-----+-----+-----+------+-----+-----+----+-----+-----+-------+-----+----+
|            | AIFF | AU | AVR | CAF | FLAC | HTK | IRCAM | MAT4 | MAT5 | MPC2K | NIST | OGG | PAF | PVF | RAW | RF64 | SD2 | SVX | VOC| W64 | WAV | WAVEX | WVE | XI |
+============+======+====+=====+=====+======+=====+=======+======+======+=======+======+=====+=====+=====+=====+======+=====+=====+====+=====+=====+=======+=====+====+
|            |      |    |     |     |      |     |       |      |      |       |      |     |     |     |     |      |     |     |    |     |     |       |     |    |
+------------+------+----+-----+-----+------+-----+-------+------+------+-------+------+-----+-----+-----+-----+------+-----+-----+----+-----+-----+-------+-----+----+