Recommended way of working with audio files in scientific work
==============================================================

1) If the source data is an audio file, it is a good idea to keep that
original. I.e. do not delete it after you converted it into something else,
even if that conversion is said to be 'lossless' or if you are saving in a
higher resolution format. Some conversions are theoretically lossless, but
even renowned audio libraries and programs have bugs, so any conversion may
lead to unintended changes. I have seen this really happens in practice.

2) When recording audio files use a widely supported format with sufficient
resolution. 'WAV' format with 24-bit PCM encoding, or, even better though not
yet ubiquitously supported, 32-bit float LPCM encoding without compression.
These are lossless and widely used formats, reducing the chances that software
reading or writing these files have bugs that potentially change the data. The
latter format has the advantage that data can be read very fast because your
computer can directly work with 32-bit float numbers and not with 24-bit
numbers, which will need more processing.

3) The WAV format is unfortunately limited to file sizes less than 4 Gb. Recording
equipment will often generate multiple files when the 4 Gb limit is crossed.
In the Sound library, such files of consecutive audio chunks can easily be
used as one sound with the ChunkedSnd object.

4) If you change the data with some transformation and you may process it further
later, it is recommended to store the results in a 64-bit float format, if disk
space is not a major concern. If you do not need an audio file then a float64 `Darr
<https://github.com/gbeckers/Darr>`__ array is a good option because this maximizes
accessibility of your data by other scientific computing libraries and platforms.
Sound will write to Darr arrays. If you need the data to be coded in an audio format,
consider a WAV file in DOUBLE (i.e 64-bit float) format.
