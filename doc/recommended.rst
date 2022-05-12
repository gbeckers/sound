Recommended way of working with audio files in scientific work
==============================================================

Summary
-------

1) Never delete original data files (source audio files).

2) When making an audio recording choose WAV format with 24-bit PCM or 32-bit
float PCM encoding, if available.

3) For processing (scaling, filtering etc), first convert data to 64-bit float.


Explanation
-----------

1) It is a very good idea to keep original source audio files. Do not delete
them after you converted them into something else, even if that conversion is
said to be 'lossless', for example when you are just saving in a higher
resolution format. Some conversions are theoretically lossless, but even
renowned audio libraries and programs have assumptions you may not share, or
even bugs, and in practice any conversion may lead to unintended changes to
the sound waveform. I have seen this happen in practice too often.

2) When recording audio files, use a widely supported format with sufficient
resolution. 'WAV' format with 24-bit PCM encoding, or 32-bit float PCM
encoding without compression. These are lossless formats with high
resolution and they are widely used, reducing the chances that software
reading these files have bugs that potentially change the data. 32-Bit float
PCM has the advantage that data can be read very fast because your
computer can directly work with 32-bit float numbers. 24-Bit integer PCM
has the advantage that it is more standard, and uses 25% less disk space.
Its resolution is lower but still very high, likely more than you need.

The WAV format is unfortunately limited to file sizes smaller than 4 Gb.
Recording equipment will often generate multiple files when the 4 Gb limit
is crossed. However, in *Sound* such files of consecutive audio chunks can
easily be used as one sound with the ChunkedSnd object.

3) If you change the data with some transformation and you may process it
further later, it is recommended to store the results in a 64-bit float
format, if disk space is not a major concern. If you do not need an audio
file then a float64 `Darr <https://github.com/gbeckers/Darr>`__ array is a
good option because this maximizes accessibility of your data by other
scientific computing libraries and platforms. Sound will write to Darr
arrays. If you need the data to be coded in an audio format, consider a WAV
file in DOUBLE (i.e 64-bit float) format.
