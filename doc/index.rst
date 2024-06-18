Sound
=====

*Sound* is a package for working with sound data in Python. It is developed
particularly for scientific use cases and soundscape recordists/analysts.

There are various excellent tools for working with audio files in Python.
However, audio files were never designed for scientific work and can be
cumbersome to work with. Some examples include working with very long
recordings (think many hours, days, weeks) that do not fit into RAM or take
ages to load, working with zillions of short sound events, with non-integer
sampling rates (needed to precisely synchronize acoustic data with other
data), with absolute sound levels or absolute time, or various types of
metadata.

*Sound* is based on (collections of) regular audio files, ensuring
hardware/software compatibility with the audio world, but it improves
their usefulness by storing important metadata in separate text-based (JSON)
files, and, for very large collections of sound, additionally in widely
readable and self-documented binary files.

Status
------
*Sound* is in its early stages of development (alpha) stage. It will be
complemented by the *SoundLab* library for sound analysis and visualization.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   overview
   install
   recommended
   formats
   normalization
   api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Sound is BSD licensed (BSD 3-Clause License). (c) 2020-2024, Gabriël Beckers