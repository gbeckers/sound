Three options for single sounds:
- AudioFile
- AudioSnd
- DarrSnd

Options for collections of sounds:
- ChunkedSnd: continuous, but divided over multiple files
- FragmentedSnd: discontinuous
- SndDict: dictionary of single sound


json '.snd' files hold all info.

Format: file type, e.g. WAV, darr
Encoding: subtype in SF, e.g PCM16




next disksnd should be  SndInfo for all disk based snd objects (not tied to dir)

metadata -> user metadata
sndinfo -> sndmetadata
Sound objects correspond to a directory with a .snd extension. An exception are AudioFile objects,
which are just audio files e.g. wav files. A directory keeps things nicely contains (e.g. when copying
sound objects), and allows for the storage of additional (potentially large) other data whch would not
fit efficiently in the json info file.
- Directory contains a json file, sndinfo.json with information about the sound object.