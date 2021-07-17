Sound
=====

*Sound* is a package for working with acoustic data in Python. It is designed
for scientific use cases, but it may also be of interest to soundscape
recordists, or anyone who wants to work efficiently with very long sounds,
with very many sounds, or with metadata.

There already good tools for working with audio files in Python. However,
audio files can be cumbersome to work with in applications they were not
designed for. Some examples include the ability to work efficiently with very
long recordings (think many hours, days, weeks), with zillions of short sound
events, with non-integer sampling rates (needed to precisely synchronize
acoustic data with other data), with absolute sound levels or absolute time, or
various types of metadata. These things do not matter when working with your
average music song, but they do matter in science and other applications.
*Sound* is intended to solve this problem.

In its simplest form, *Sound* work with (collections of) normal audio files.
However it improves their usefulness by organizing important metadata in
separate text-based files. For more heavy-duty work, *Sound* works with
`Darr <https://darr.readthedocs.io/en/latest>`__-based data, which is a format
designed for scientific use and supports very efficient random access
reading/writing of numeric data. This way, you can efficiently work very
large recordings (that won't fit in RAM memory), or zillions of recorded
sound episodes which would otherwise be inefficiently stored in zillions of
separate files.

*Sound* is in its early stages of development (alpha) stage. It forms the basis
of, and is complemented, by the *SoundLab* library for sound analysis and
visualization, and *SoundStimBuilder* library for those who construct auditory
stimuli, e.g. for scientific experiments.

Sound is BSD licensed (BSD 3-Clause License). (c) 2020, Gabriël Beckers


