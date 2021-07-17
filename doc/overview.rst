==============
Sound Overview
==============

The purpose of Sound is to provide a Python library for working with disk-based sound
data. Simple audio files are not sufficient for scientific practice, although they can
be part of it. How to work with very long recordings for example? Or zillions of sound
events? Or non-integer sampling rates? Or metadata?

The Sound library tries to make your life easier and your work more reproducible by
addressing such issues.

Understanding disk-based sound data in Sound
--------------------------------------------
Under the hood Sound can use two ways in which sound data is stored on disk.

1) Data is stored in one or more *audio* files (all file formats that
are supported by the external `SoundFile <https://https://pypi.org/project/SoundFile/>`__
library). Metadata is saved in additional text-based files (JSON). The
advantage of audio files is that you can easily open them in audio software,
for instance to play them. The simplest object that uses this format is an
AudioSnd. It is simply consists of an audio file with metadata
in a separate text file.

2) Data is stored in `Darr <https://darr.readthedocs.io/en/latest>`__ format.
The advantage is that it is often much faster to read, which helps if you
need to access many random parts of large sounds, or large sequences of
sounds quickly. Also, Darr is an open format for scientific data that makes
your data accessible in data analysis platforms as it does not depend on
tool-specific formats. Further,

Main Object Types in the Sound library
--------------------------------------
**Snd**: A simple continuous sound with metadata, stored on RAM memory.

**AudioSnd**: A simple continuous sound, stored on disk in audio format. If you
have an existing audio file and want to convert it to an AudioSnd, use the
AudioFile object and its as_audiosnd method. The audio file remains the same
the same, but AudioSnd allows additionally for text-based metadata, and
non-integer sampling rates.

**DarrSnd**: A simple continuous sound, stored on disk in Darr format.

**ChunkedSnd**: A simple continuous sound, stored as consecutive chunks in separate
files, either audio or darr format. This can be convenient when sounds are very long.
Audio recorders for example will save sequences of files when the recording is longer
than the file system allows for in terms of file size.

**FragementedSnd**: A continuous sound, of which only fragments with known time
occurrences are available. For example, a sound recorder only saves interesting events
from continuous input. A FragmentedSnd is a simple way of representing the complete
sound. It will fill in the 'missing' frames with zeros when they are read.
FragementedSnd objects can be based on either audio or darr format.

Many of these objects can be converted to another object type by dedicated object
methods.


