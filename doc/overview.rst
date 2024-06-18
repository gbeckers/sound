==============
Sound Overview
==============

Sound is a Python library for working with disk-based sound data, focusing on
scientific applications. It should make your life easier with often
encountered problems. How to efficiently work with very long recordings for
example? Or zillions of sound events? Or non-integer sampling rates? Or
metadata?

The Sound library aims to make your work more efficient and reproducible by
addressing such issues.

Understanding disk-based sound data in Sound
--------------------------------------------
Under the hood Sound can use two ways in which sound data is stored on disk.

1) Data is stored in one or more regular *audio* files (all file formats that
are supported by the external `SoundFile <https://https://pypi.org/project/SoundFile/>`__
library). Metadata is saved in additional text-based files (JSON). The
advantage of using audio files is that you can easily open them in audio
software, for instance to play them. The simplest object that uses this
format is an AudioSnd. It is simply consists of an audio file with metadata
in a separate text file.

2) Data is stored in `Darr <https://darr.readthedocs.io/en/latest>`__ format.
The advantage is that it is often much faster to read, which helps if you
need to access many random parts of large sounds, or large sequences of
sounds quickly. Also, Darr is an open format for scientific data that makes
your data accessible in data analysis platforms as it does not depend on
tool-specific formats.

Main Object Types in the Sound library
--------------------------------------
**AudioFileSnd**: A continuous sound, with data stored on disk in a regular
audio file and a separate text-based (json) metadata file. The metadata file
allows for storing standard information about the sound (e.g. recording date
and time, place) as well as any extra user information. This metadata has
priority over metadata in the audiofile itself, which can be handy, for example
when specifying non-integer sampling rates (audio files often only support
integer sampling rates, which is not always precise enough for scientific
purposes).

**ChunkedSnd**: A continuous sound, stored as consecutive chunks in
separate audio files. This can be convenient when sound recordings are very
long. For example, audio recorders will often save sounds in a sequence of
separate audio files when the file size would become larger than a file system
allows for. In sound, chunks in separate audio files are virtually merged and
can be accessed as long sound object. This way, it becomes trivially easy and
fast to select, e.g., a fragment from 5 to 7 AM on the fifth day of a week-long
recording.

**FragementedSnd**: A continuous sound, of which only fragments have been stored.
For example, a sound recorder only saves interesting events from continuous input.
A FragmentedSnd provides a simple way of representing the complete recording as one
sound object, filling in the 'missing' frames with zeros when they are read.

**Snd**: A continuous sound with metadata, stored on RAM memory.

Many of these objects can be converted to another object type by dedicated object
methods.


