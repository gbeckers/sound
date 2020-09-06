Sound
=====

*Sound* is a package for working with acoustic data in Python. It is designed
for scientific use cases, but it may also be of interest to soundscape
recordists, or anyone who wants to work efficiently with very long sounds,
with very many sounds, or with metadata.

There already exist good tools for working with audio files in Python. However,
audio files can be cumbersome to work with in applications they were not
designed for. Some examples include the ability to work efficiently with very
long recordings (think many hours, days, weeks), with zillions of short sound
events, with non-integer sampling rates (needed to precisely synchronize
acoustic data with other data), with absolute sound levels or absolute time, or
with metadata. These things do not matter for working with your average music
song, but they do matter in science and other applications. *Sound* is intended
to solve this problem.

*Sound* can work with (collections of) normal audio files, but it improves their
usefulness by organizing important metadata in separate text-based files. In
addition, *Sound* can work with
`Darr <https://darr.readthedocs.io/en/latest>`__-based data, which is a format
designed for scientific use and very fast random access read/write speed.

*Sound* is in its early stages of development (alpha) stage. It forms the basis
of, and is complemented, by the *SoundLab* library for sound analysis and
visualization, and *SoundStimBuilder* library for those who construct auditory
stimuli, e.g. for scientific experiments.

Status
------
Sound is relatively new, and therefore in its alpha stage.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   install
   recommended
   api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Sound is BSD licensed (BSD 3-Clause License). (c) 2020, Gabriël Beckers