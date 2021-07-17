- Sound objects correspond to a directory with a .snd extension. An exception are AudioFile objects,
which are just audio files e.g. wav files. A directory keeps things nicely contains (e.g. when copying
sound objects), and allows for the storage of additional (potentially large) other data whch would not
fit efficiently in the json info file.
- Directory contains a json file, sndinfo.json with information about the sound object.