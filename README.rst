Sound
=====

**NOTE: DO NOT USE THIS VERSION YET, in middle of refactoring.**

Sound
=====

*Sound* is a package for working with sound data in Python. It is designed
for scientific use cases, but it may also be of interest to soundscape
recordists, or anyone who wants to work efficiently with very long sounds,
with very many sounds, or with metadata.

There are various excellent tools for working with audio files in Python.
However, audio files can be cumbersome to work with in scientific
applications because they were not designed for this type of work in mind.

Some examples include working efficiently with very long recordings
(think many hours, days, weeks) that do not fit into RAM, with zillions of
short sound events, with non-integer sampling rates (needed to precisely
synchronize acoustic data with other data, or simply for accuracy), with
absolute sound levels or absolute time, or various types of metadata. These
things do not matter when playing music or speech on an audio device, but
they matter in scientific work and other applications.

*Sound* is intended to solve such problems.

In its simplest use case, *Sound* works with (collections of) normal audio
files. This ensures hardware/software compatibility with the audio world.
However it improves their usefulness by organizing important metadata in
separate text-based (JSON) files.

For more heavy-duty work, *Sound* works with
`Darr <https://darr.readthedocs.io/en/latest>`__-based data, which is a format
designed for scientific use and supports very efficient random access
reading/writing of disk-based numeric data. This way, you can work
very large recordings, or zillions of recorded sound episodes which would
otherwise be inefficiently stored in separate files. It also
ensures your sound data can easily be used in various scientific computing
environments.

Status
------
*Sound* is in its early stages of development (alpha) stage. It will be
complemented by the *SoundLab* library for sound analysis and visualization.

Sound is BSD licensed (BSD 3-Clause License). (c) 2020-2024, Gabriël Beckers


